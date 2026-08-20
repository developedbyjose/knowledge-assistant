from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_auth_service, get_current_user, get_knowledge_base_service
from app.main import app


def user(*, role="user", must_change_password=False):  # noqa: ANN001, ANN201
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(), email="person@example.com", display_name="Person", role=role,
        is_active=True, must_change_password=must_change_password,
        created_at=now, updated_at=now, last_login_at=None,
    )


class FakeAuthService:
    def __init__(self, current=None):  # noqa: ANN001
        self.user = current or user()
        self.logged_out = False

    def authenticate(self, *, email, password):  # noqa: ANN001, ANN201
        return self.user

    def create_session(self, _user):  # noqa: ANN001, ANN201
        return "raw-session-token"

    def current_user(self, token):  # noqa: ANN001, ANN201
        return self.user if token == "raw-session-token" else None

    def logout(self, token):  # noqa: ANN001, ANN201
        self.logged_out = True


class FakeKnowledgeBases:
    def list(self, *, active_only=False):  # noqa: ANN001, ANN201
        return []


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_login_sets_http_only_same_site_cookie_and_me_reads_it() -> None:
    service = FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    response = client.post("/api/v1/auth/login", json={"email": "PERSON@example.com", "password": "temporary-password"})
    me = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert me.status_code == 200
    assert me.json()["email"] == "person@example.com"


def test_product_routes_require_authentication() -> None:
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBases()

    response = TestClient(app).get("/api/v1/knowledge-bases")

    assert response.status_code == 401


def test_normal_user_cannot_create_knowledge_base() -> None:
    app.dependency_overrides[get_current_user] = lambda: user(role="user")
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBases()

    response = TestClient(app).post("/api/v1/knowledge-bases", json={"name": "Private"})

    assert response.status_code == 403


def test_temporary_password_blocks_product_routes_but_not_me() -> None:
    temporary_user = user(must_change_password=True)
    app.dependency_overrides[get_current_user] = lambda: temporary_user
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBases()
    client = TestClient(app)

    assert client.get("/api/v1/auth/me").status_code == 200
    blocked = client.get("/api/v1/knowledge-bases")
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "Password change required."


def test_cookie_authenticated_cross_origin_write_is_rejected() -> None:
    service = FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)
    client.cookies.set("knowledge_assistant_session", "raw-session-token")

    response = client.post("/api/v1/auth/logout", headers={"Origin": "https://malicious.example"})

    assert response.status_code == 403
    assert service.logged_out is False
