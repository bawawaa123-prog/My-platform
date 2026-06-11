from fastapi.testclient import TestClient


def test_login_returns_access_token_and_current_user(client: TestClient) -> None:
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@example.com",
            "password": "admin123",
        },
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "admin@example.com"
    assert body["user"]["role"] == "admin"

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "admin@example.com"
