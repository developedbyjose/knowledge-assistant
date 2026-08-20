from app.core.security import hash_password, hash_session_token, new_session_token, verify_password


def test_passwords_are_argon2_hashed_and_verified() -> None:
    encoded = hash_password("correct horse battery staple")

    assert encoded.startswith("$argon2")
    assert verify_password(encoded, "correct horse battery staple") is True
    assert verify_password(encoded, "wrong password") is False


def test_session_tokens_are_random_and_only_hashes_are_persistable() -> None:
    first = new_session_token()
    second = new_session_token()

    assert first != second
    assert len(hash_session_token(first)) == 64
    assert first not in hash_session_token(first)
