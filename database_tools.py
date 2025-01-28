import sqlite3

from datetime import datetime

DB_PATH = 'parking.db'  # Ścieżka do pliku bazy danych

# Funkcja inicjalizująca bazę danych
def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_parking_event(plate_number: str, action: str):
    """
    Dodaje zdarzenie do bazy danych.

    :param plate_number: Numer rejestracyjny samochodu
    :param action: Akcja (ENTRY lub EXIT)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO parking_log (plate_number, action, timestamp) VALUES (?, ?, ?)",
        (plate_number, action, timestamp)
    )
    conn.commit()
    conn.close()

def get_parking_log():
    """
    Pobiera pełny log parkingu z bazy danych.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parking_log")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_event(plate_number: str):
    """
    Pobiera ostatnie zdarzenie dla danego numeru rejestracyjnego.

    :param plate_number: Numer rejestracyjny samochodu
    :return: Słownik z informacjami o ostatnim zdarzeniu (akcja, czas jako float) lub None
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT action, timestamp
        FROM parking_log
        WHERE plate_number = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (plate_number,))
    result = cursor.fetchone()
    connection.close()
    
    if result:
        # Konwertuj timestamp na float (czas w sekundach od epoki UNIX)
        timestamp_str = result[1]  # Zakładamy, że timestamp to string w formacie 'YYYY-MM-DD HH:MM:SS'
        timestamp_float = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp()
        return {"action": result[0], "timestamp": timestamp_float}
    return None