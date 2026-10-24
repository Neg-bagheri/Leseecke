import pytest
from fastapi.testclient import TestClient

import database
from main import app


@pytest.fixture
def client(tmp_path):
    # use a separate database for every test
    database.DB_FILE = tmp_path / "test.db"
    database.create_tables()
    return TestClient(app)


def test_get_all_books(client):
    response = client.get("/api/books")
    assert response.status_code == 200
    assert len(response.json()) == 18


def test_search(client):
    response = client.get("/api/books", params={"q": "kafka"})
    titles = [book["title"] for book in response.json()]
    assert titles == ["Der Process", "Die Verwandlung"]


def test_add_book(client):
    new_book = {"title": "Tschick", "author": "Wolfgang Herrndorf", "year": 2010, "category": "Jugendbuch"}
    response = client.post("/api/books", json=new_book)
    assert response.status_code == 200
    assert response.json()["title"] == "Tschick"
    assert response.json()["available"] is True


def test_borrow_and_return(client):
    response = client.post("/api/books/1/borrow", json={"borrower": "Anna", "days": 7})
    assert response.json()["available"] is False

    response = client.post("/api/books/1/borrow", json={"borrower": "Tom"})
    assert response.status_code == 400

    response = client.post("/api/books/1/return")
    assert response.json()["available"] is True


def test_cannot_delete_borrowed_book(client):
    response = client.delete("/api/books/3")
    assert response.status_code == 400


def test_book_not_found(client):
    response = client.get("/api/books/999")
    assert response.status_code == 404
