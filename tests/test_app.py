import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            "Chess Club": {
                "description": "Play chess",
                "schedule": "Fridays",
                "max_participants": 2,
                "participants": ["existing@mergington.edu"],
            },
            "Art Club": {
                "description": "Make art",
                "schedule": "Wednesdays",
                "max_participants": 10,
                "participants": [],
            },
        },
    )
    return TestClient(app_module.app)


def test_root_redirects_to_homepage(client):
    response = client.get("/")

    assert response.history
    assert response.history[0].status_code == 307
    assert response.history[0].headers["location"] == "/static/index.html"
    assert response.status_code == 200


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == ["existing@mergington.edu"]
    assert response.json()["Art Club"]["participants"] == []


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@mergington.edu for Chess Club"}
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == ["existing@mergington.edu", "new@mergington.edu"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == ["existing@mergington.edu"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@mergington.edu from Chess Club"
    }
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == []


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "unknown@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
