from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from models import Author as AuthorModel
from models import Book as BookModel

app = FastAPI(title="Library Management System API")

# Pydantic модели для API
# Author schemas
class AuthorBase(BaseModel):
    name: str
    birth_year: Optional[int] = None
    country: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class AuthorUpdate(BaseModel):
    name: Optional[str] = None
    birth_year: Optional[int] = None
    country: Optional[str] = None

class AuthorResponse(AuthorBase):
    id: int
    books_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class BookBase(BaseModel):
    title: str
    isbn: str
    publication_year: Optional[int] = None
    genre: Optional[str] = None
    author_id: int

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    genre: Optional[str] = None
    author_id: Optional[int] = None

class BookResponse(BookBase):
    id: int
    author_name: Optional[str] = None
    
    class Config:
        from_attributes = True

@app.post("/authors/", response_model=AuthorResponse, status_code=201)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    db_author = AuthorModel(**author.model_dump())
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.get("/authors/", response_model=List[AuthorResponse])
def get_authors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    authors = db.query(AuthorModel).offset(skip).limit(limit).all()
    
    result = []
    for author in authors:
        author_dict = {
            "id": author.id,
            "name": author.name,
            "birth_year": author.birth_year,
            "country": author.country,
            "books_count": len(author.books)
        }
        result.append(author_dict)
    
    return result

@app.get("/authors/{author_id}", response_model=AuthorResponse)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(AuthorModel).filter(AuthorModel.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return {
        "id": author.id,
        "name": author.name,
        "birth_year": author.birth_year,
        "country": author.country,
        "books_count": len(author.books)
    }

@app.put("/authors/{author_id}", response_model=AuthorResponse)
def update_author(author_id: int, author_update: AuthorUpdate, db: Session = Depends(get_db)):
    author = db.query(AuthorModel).filter(AuthorModel.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    update_data = author_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(author, field, value)
    
    db.commit()
    db.refresh(author)
    
    return {
        "id": author.id,
        "name": author.name,
        "birth_year": author.birth_year,
        "country": author.country,
        "books_count": len(author.books)
    }

@app.delete("/authors/{author_id}")
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(AuthorModel).filter(AuthorModel.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    db.delete(author)
    db.commit()
    return {"message": "Author and all their books deleted successfully"}

# API Endpoints для Книг
@app.post("/books/", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    author = db.query(AuthorModel).filter(AuthorModel.id == book.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    existing_book = db.query(BookModel).filter(BookModel.isbn == book.isbn).first()
    if existing_book:
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    db_book = BookModel(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    return {
        "id": db_book.id,
        "title": db_book.title,
        "isbn": db_book.isbn,
        "publication_year": db_book.publication_year,
        "genre": db_book.genre,
        "author_id": db_book.author_id,
        "author_name": author.name
    }

@app.get("/books/", response_model=List[BookResponse])
def get_books(
    skip: int = 0, 
    limit: int = 100, 
    author_id: Optional[int] = None,
    genre: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(BookModel)
    
    if author_id:
        query = query.filter(BookModel.author_id == author_id)
    if genre:
        query = query.filter(BookModel.genre == genre)
    
    books = query.offset(skip).limit(limit).all()
    
    result = []
    for book in books:
        result.append({
            "id": book.id,
            "title": book.title,
            "isbn": book.isbn,
            "publication_year": book.publication_year,
            "genre": book.genre,
            "author_id": book.author_id,
            "author_name": book.author.name if book.author else None
        })
    
    return result

@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {
        "id": book.id,
        "title": book.title,
        "isbn": book.isbn,
        "publication_year": book.publication_year,
        "genre": book.genre,
        "author_id": book.author_id,
        "author_name": book.author.name if book.author else None
    }

@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book_update: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book_update.author_id:
        author = db.query(AuthorModel).filter(AuthorModel.id == book_update.author_id).first()
        if not author:
            raise HTTPException(status_code=404, detail="New author not found")
    
    if book_update.isbn and book_update.isbn != book.isbn:
        existing_book = db.query(BookModel).filter(BookModel.isbn == book_update.isbn).first()
        if existing_book:
            raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    update_data = book_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    
    db.commit()
    db.refresh(book)
    
    return {
        "id": book.id,
        "title": book.title,
        "isbn": book.isbn,
        "publication_year": book.publication_year,
        "genre": book.genre,
        "author_id": book.author_id,
        "author_name": book.author.name if book.author else None
    }

@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully"}

@app.get("/authors/{author_id}/books", response_model=List[BookResponse])
def get_author_books(author_id: int, db: Session = Depends(get_db)):
    author = db.query(AuthorModel).filter(AuthorModel.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    result = []
    for book in author.books:
        result.append({
            "id": book.id,
            "title": book.title,
            "isbn": book.isbn,
            "publication_year": book.publication_year,
            "genre": book.genre,
            "author_id": book.author_id,
            "author_name": author.name
        })
    
    return result

@app.get("/search/")
def search_books(q: str, db: Session = Depends(get_db)):
    books = db.query(BookModel).join(AuthorModel).filter(
        (BookModel.title.ilike(f"%{q}%")) | 
        (AuthorModel.name.ilike(f"%{q}%"))
    ).all()
    
    result = []
    for book in books:
        result.append({
            "id": book.id,
            "title": book.title,
            "author": book.author.name if book.author else None,
            "isbn": book.isbn,
            "genre": book.genre
        })
    
    return result
