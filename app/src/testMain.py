import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import get_db
from models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_author():
    response = client.post("/authors/", json={
        "name": "Тестовый Автор",
        "birth_year": 1990,
        "country": "Россия"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Тестовый Автор"
    assert data["birth_year"] == 1990
    assert data["country"] == "Россия"
    assert "id" in data


def test_get_authors():
    client.post("/authors/", json={"name": "Автор 1", "birth_year": 1990})
    client.post("/authors/", json={"name": "Автор 2", "birth_year": 1991})
    
    response = client.get("/authors/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_author_by_id():
    create_response = client.post("/authors/", json={
        "name": "Тестовый Автор",
        "birth_year": 1990,
        "country": "Россия"
    })
    author_id = create_response.json()["id"]
    
    response = client.get(f"/authors/{author_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Тестовый Автор"
    assert data["id"] == author_id


def test_get_author_not_found():
    response = client.get("/authors/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Author not found"


def test_update_author():
    create_response = client.post("/authors/", json={
        "name": "Старое Имя",
        "birth_year": 1990
    })
    author_id = create_response.json()["id"]
    
    response = client.put(f"/authors/{author_id}", json={
        "name": "Новое Имя",
        "country": "Новая Страна"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Новое Имя"
    assert data["country"] == "Новая Страна"


def test_delete_author():
    create_response = client.post("/authors/", json={"name": "Автор для удаления"})
    author_id = create_response.json()["id"]
    
    response = client.delete(f"/authors/{author_id}")
    assert response.status_code == 200
    
    get_response = client.get(f"/authors/{author_id}")
    assert get_response.status_code == 404

def test_create_book():
    author_response = client.post("/authors/", json={"name": "Автор книги"})
    author_id = author_response.json()["id"]
    
    response = client.post("/books/", json={
        "title": "Тестовая Книга",
        "isbn": "978-5-17-123456-7",
        "publication_year": 2020,
        "genre": "Фантастика",
        "author_id": author_id
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая Книга"
    assert data["author_id"] == author_id


def test_create_book_duplicate_isbn():
    author_response = client.post("/authors/", json={"name": "Автор"})
    author_id = author_response.json()["id"]
    
    client.post("/books/", json={
        "title": "Книга 1",
        "isbn": "978-5-17-111111-1",
        "author_id": author_id
    })
    
    response = client.post("/books/", json={
        "title": "Книга 2",
        "isbn": "978-5-17-111111-1",  # Тот же ISBN
        "author_id": author_id
    })
    assert response.status_code == 400
    assert "ISBN already exists" in response.json()["detail"]


def test_get_books():
    author_response = client.post("/authors/", json={"name": "Автор"})
    author_id = author_response.json()["id"]
    
    client.post("/books/", json={
        "title": "Книга 1",
        "isbn": "978-5-17-111111-1",
        "author_id": author_id
    })
    client.post("/books/", json={
        "title": "Книга 2",
        "isbn": "978-5-17-222222-2",
        "author_id": author_id
    })
    
    response = client.get("/books/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_filter_books_by_author():
    author1 = client.post("/authors/", json={"name": "Автор 1"}).json()
    author2 = client.post("/authors/", json={"name": "Автор 2"}).json()
    
    client.post("/books/", json={
        "title": "Книга Автора 1",
        "isbn": "978-5-17-111111-1",
        "author_id": author1["id"]
    })
    client.post("/books/", json={
        "title": "Книга Автора 2",
        "isbn": "978-5-17-222222-2",
        "author_id": author2["id"]
    })
    
    response = client.get(f"/books/?author_id={author1['id']}")
    data = response.json()
    for book in data:
        assert book["author_id"] == author1["id"]


def test_filter_books_by_genre():
    author_response = client.post("/authors/", json={"name": "Автор"})
    author_id = author_response.json()["id"]
    
    client.post("/books/", json={
        "title": "Роман",
        "isbn": "978-5-17-111111-1",
        "genre": "Роман",
        "author_id": author_id
    })
    client.post("/books/", json={
        "title": "Фантастика",
        "isbn": "978-5-17-222222-2",
        "genre": "Фантастика",
        "author_id": author_id
    })
    
    response = client.get("/books/?genre=Роман")
    data = response.json()
    for book in data:
        assert book["genre"] == "Роман"


def test_update_book():
    author_response = client.post("/authors/", json={"name": "Автор"})
    author_id = author_response.json()["id"]
    
    create_response = client.post("/books/", json={
        "title": "Старое Название",
        "isbn": "978-5-17-111111-1",
        "author_id": author_id
    })
    book_id = create_response.json()["id"]
    
    response = client.put(f"/books/{book_id}", json={
        "title": "Новое Название",
        "genre": "Новый Жанр"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Новое Название"
    assert data["genre"] == "Новый Жанр"


def test_delete_book():
    author_response = client.post("/authors/", json={"name": "Автор"})
    author_id = author_response.json()["id"]
    
    create_response = client.post("/books/", json={
        "title": "Книга для удаления",
        "isbn": "978-5-17-111111-1",
        "author_id": author_id
    })
    book_id = create_response.json()["id"]
    
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 200
    
    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 404


def test_get_author_books():
    author_response = client.post("/authors/", json={"name": "Автор"})
    author_id = author_response.json()["id"]
    
    client.post("/books/", json={
        "title": "Книга 1",
        "isbn": "978-5-17-111111-1",
        "author_id": author_id
    })
    client.post("/books/", json={
        "title": "Книга 2",
        "isbn": "978-5-17-222222-2",
        "author_id": author_id
    })
    
    response = client.get(f"/authors/{author_id}/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_search_books():
    author_response = client.post("/authors/", json={"name": "Пушкин"})
    author_id = author_response.json()["id"]
    
    client.post("/books/", json={
        "title": "Евгений Онегин",
        "isbn": "978-5-17-111111-1",
        "author_id": author_id
    })
    
    response = client.get("/search/?q=Онегин")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "Онегин" in data[0]["title"]