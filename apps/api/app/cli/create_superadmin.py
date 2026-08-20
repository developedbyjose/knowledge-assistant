from __future__ import annotations

import argparse
import getpass

from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth_service import normalize_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the initial Knowledge Assistant superadmin.")
    parser.add_argument("--email", help="Superadmin email; prompted when omitted.")
    parser.add_argument("--display-name", help="Display name; prompted when omitted.")
    args = parser.parse_args()

    email = normalize_email(args.email or input("Email: "))
    display_name = (args.display_name or input("Display name: ")).strip()
    password = getpass.getpass("Password (12-128 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    if not 12 <= len(password) <= 128:
        raise SystemExit("Password must be 12-128 characters.")
    if not email or not display_name:
        raise SystemExit("Email and display name are required.")

    with SessionLocal() as session:
        session.add(
            User(
                email=email,
                display_name=display_name,
                password_hash=hash_password(password),
                role="superadmin",
                is_active=True,
                must_change_password=False,
            )
        )
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise SystemExit("A user with this email already exists.") from exc

    print(f"Created superadmin {email}.")


if __name__ == "__main__":
    main()
