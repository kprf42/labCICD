## описание
2 таблицы: авторы (Authors), книги (Books)

## технологии
Python
PostgreSQL
Docker + Docker Compose

Создайте файл .env с настройками:
   -- POSTGRES_PASSWORD=supersecret123
   -- DATABASE_URL=postgresql://user:supersecret123@db:5432/librarydb

## запросы 
на порту http://localhost:8000

--создать втора 
POST http://localhost:8000/authors/
Content-Type: application/json

{
  "name": "string",
  "birth_year": 0,
  "country": "string"
}

-- получить всех авторов 
GET http://localhost:8000/authors/

-- получить автора по id 
GET http://localhost:8000/authors/id 

-- обновить автора
PUT http://localhost:8000/authors/id

-- удалить автора
DELETE http://localhost:8000/authors/id

-- создать книгу 
POST http://localhost:8000/books/
{
  "title": "string",
  "isbn": "978-5-17-123456-1",
  "publication_year": 0,
  "genre": "string",
  "author_id": 1
}

-- получить все книги
GET http://localhost:8000/books/

-- подучить книгу по id 
GET http://localhost:8000/books/id

-- обновить книгу 
PUT http://localhost:8000/books/id

-- удалить книгу
DELETE http://localhost:8000/books/id

-- книга автора
GET http://localhost:8000/authors/2/books
