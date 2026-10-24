from datetime import date, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import create_tables, get_connection

app = FastAPI(title="Leseecke")
app.mount("/static", StaticFiles(directory="static"), name="static")

create_tables()


class BookIn(BaseModel):
    title: str
    author: str
    year: int
    category: str
    description: str = ""


class BorrowIn(BaseModel):
    borrower: str
    days: int = 14


def book_to_dict(row):
    book = dict(row)
    today = date.today().isoformat()
    book["available"] = book["borrower"] is None
    book["overdue"] = book["due_date"] is not None and book["due_date"] < today
    return book


def find_book(conn, book_id):
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Buch nicht gefunden")
    return book_to_dict(row)


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/api/books")
def get_books(q: str = "", category: str = "", status: str = "", sort: str = "title"):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM books").fetchall()
    conn.close()

    q = q.lower()
    result = []

    for row in rows:
        book = book_to_dict(row)

        if q not in book["title"].lower() and q not in book["author"].lower():
            continue
        if category != "" and book["category"] != category:
            continue
        if status == "available" and not book["available"]:
            continue
        if status == "borrowed" and book["available"]:
            continue
        if status == "overdue" and not book["overdue"]:
            continue

        result.append(book)

    if sort == "author":
        result.sort(key=lambda b: b["author"])
    elif sort == "year":
        result.sort(key=lambda b: b["year"])
    elif sort == "year_desc":
        result.sort(key=lambda b: b["year"], reverse=True)
    else:
        result.sort(key=lambda b: b["title"])

    return result


@app.get("/api/books/{book_id}")
def get_book(book_id: int):
    conn = get_connection()
    book = find_book(conn, book_id)
    conn.close()
    return book


@app.post("/api/books")
def add_book(new_book: BookIn):
    if new_book.title.strip() == "" or new_book.author.strip() == "":
        raise HTTPException(status_code=400, detail="Titel und Autor dürfen nicht leer sein")

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO books (title, author, year, category, description) VALUES (?, ?, ?, ?, ?)",
        (new_book.title.strip(), new_book.author.strip(), new_book.year,
         new_book.category.strip(), new_book.description.strip()),
    )
    conn.commit()
    book = find_book(conn, cursor.lastrowid)
    conn.close()
    return book


@app.delete("/api/books/{book_id}")
def delete_book(book_id: int):
    conn = get_connection()
    book = find_book(conn, book_id)

    if not book["available"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Ausgeliehene Bücher können nicht gelöscht werden")

    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return {"message": "Buch gelöscht"}


@app.post("/api/books/{book_id}/borrow")
def borrow_book(book_id: int, data: BorrowIn):
    if data.borrower.strip() == "":
        raise HTTPException(status_code=400, detail="Bitte einen Namen eingeben")

    conn = get_connection()
    book = find_book(conn, book_id)

    if not book["available"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Dieses Buch ist schon ausgeliehen")

    due_date = date.today() + timedelta(days=data.days)
    conn.execute(
        "UPDATE books SET borrower = ?, due_date = ? WHERE id = ?",
        (data.borrower.strip(), due_date.isoformat(), book_id),
    )
    conn.commit()
    book = find_book(conn, book_id)
    conn.close()
    return book


@app.post("/api/books/{book_id}/return")
def return_book(book_id: int):
    conn = get_connection()
    book = find_book(conn, book_id)

    if book["available"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Dieses Buch ist nicht ausgeliehen")

    conn.execute("UPDATE books SET borrower = NULL, due_date = NULL WHERE id = ?", (book_id,))
    conn.commit()
    book = find_book(conn, book_id)
    conn.close()
    return book


@app.get("/api/categories")
def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT category FROM books ORDER BY category").fetchall()
    conn.close()
    return [row["category"] for row in rows]


@app.get("/api/stats")
def get_stats():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM books").fetchall()
    conn.close()

    books = [book_to_dict(row) for row in rows]
    available = len([b for b in books if b["available"]])
    overdue = len([b for b in books if b["overdue"]])

    return {
        "total": len(books),
        "available": available,
        "borrowed": len(books) - available,
        "overdue": overdue,
    }
