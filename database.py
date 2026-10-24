import sqlite3
from datetime import date, timedelta

DB_FILE = "library.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT DEFAULT '',
            borrower TEXT,
            due_date TEXT
        )
    """)

    count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if count == 0:
        add_sample_books(conn)

    conn.commit()
    conn.close()


def add_sample_books(conn):
    today = date.today()

    books = [
        ("Faust", "Johann Wolfgang von Goethe", 1808, "Drama",
         "Der Gelehrte Heinrich Faust schließt einen Pakt mit dem Teufel Mephisto, um zu erkennen, was die Welt im Innersten zusammenhält."),
        ("Die Leiden des jungen Werthers", "Johann Wolfgang von Goethe", 1774, "Roman",
         "Ein junger Mann verliebt sich unglücklich in die verlobte Lotte. Der Briefroman machte Goethe über Nacht berühmt."),
        ("Die Räuber", "Friedrich Schiller", 1781, "Drama",
         "Zwei ungleiche Brüder, Intrigen und eine Räuberbande: Schillers wildes Erstlingsdrama über Freiheit und Gerechtigkeit."),
        ("Effi Briest", "Theodor Fontane", 1895, "Roman",
         "Die junge Effi wird mit einem viel älteren Baron verheiratet. Ein stiller Roman über gesellschaftliche Zwänge im 19. Jahrhundert."),
        ("Buddenbrooks", "Thomas Mann", 1901, "Roman",
         "Der Verfall einer Lübecker Kaufmannsfamilie über vier Generationen. Thomas Manns erster großer Roman."),
        ("Der Zauberberg", "Thomas Mann", 1924, "Roman",
         "Hans Castorp besucht seinen Vetter in einem Sanatorium in Davos und bleibt sieben Jahre."),
        ("Die Verwandlung", "Franz Kafka", 1915, "Erzählung",
         "Gregor Samsa erwacht eines Morgens als riesiges Insekt. Kafkas bekannteste Erzählung."),
        ("Der Process", "Franz Kafka", 1925, "Roman",
         "Josef K. wird verhaftet, ohne zu wissen, warum. Ein beklemmender Roman über eine undurchschaubare Macht."),
        ("Siddhartha", "Hermann Hesse", 1922, "Roman",
         "Ein junger Brahmane sucht auf seinem Lebensweg nach Erleuchtung und innerem Frieden."),
        ("Der Steppenwolf", "Hermann Hesse", 1927, "Roman",
         "Harry Haller fühlt sich zwischen Mensch und Wolf zerrissen, bis er in eine fremde, magische Welt eintaucht."),
        ("Im Westen nichts Neues", "Erich Maria Remarque", 1929, "Roman",
         "Der junge Soldat Paul Bäumer erlebt die Schrecken des Ersten Weltkriegs an der Westfront."),
        ("Emil und die Detektive", "Erich Kästner", 1929, "Kinderbuch",
         "Emil wird im Zug nach Berlin bestohlen und jagt den Dieb mit einer Bande Berliner Kinder."),
        ("Die Blechtrommel", "Günter Grass", 1959, "Roman",
         "Oskar Matzerath beschließt mit drei Jahren, nicht mehr zu wachsen, und erzählt deutsche Geschichte aus seiner Sicht."),
        ("Momo", "Michael Ende", 1973, "Kinderbuch",
         "Das Mädchen Momo kämpft gegen die grauen Herren, die den Menschen ihre Zeit stehlen."),
        ("Die unendliche Geschichte", "Michael Ende", 1979, "Kinderbuch",
         "Bastian liest ein geheimnisvolles Buch und wird selbst Teil der Welt Phantásien."),
        ("Das Parfum", "Patrick Süskind", 1985, "Roman",
         "Jean-Baptiste Grenouille besitzt einen unvergleichlichen Geruchssinn und jagt dem perfekten Duft nach."),
        ("Der Vorleser", "Bernhard Schlink", 1995, "Roman",
         "Der junge Michael verliebt sich in die ältere Hanna, deren Vergangenheit ihn Jahre später einholt."),
        ("Die Vermessung der Welt", "Daniel Kehlmann", 2005, "Roman",
         "Die Lebenswege von Carl Friedrich Gauß und Alexander von Humboldt, humorvoll erzählt."),
    ]

    for book in books:
        conn.execute(
            "INSERT INTO books (title, author, year, category, description) VALUES (?, ?, ?, ?, ?)",
            book,
        )

    # some example loans, so the app does not look empty
    loans = [
        (3, "Lena Schmidt", today - timedelta(days=6)),
        (6, "Jonas Weber", today + timedelta(days=9)),
        (10, "Mia Fischer", today + timedelta(days=12)),
        (15, "Paul Wagner", today - timedelta(days=2)),
    ]

    for book_id, borrower, due_date in loans:
        conn.execute(
            "UPDATE books SET borrower = ?, due_date = ? WHERE id = ?",
            (borrower, due_date.isoformat(), book_id),
        )
