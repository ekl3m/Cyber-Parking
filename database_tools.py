import sqlite3

from datetime import datetime
from log_tools import log_event

DB_PATH = 'parking.db'  # Ścieżka do pliku bazy danych

# Funkcja do inicjalizacji bazy danych
def init_database():
    """Inicjalizuje bazę danych i tworzy wymagane tabele."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela logów wjazdu/wyjazdu pojazdów
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    # Tabela do przechowywania statusów miejsc parkingowych
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numer_miejsca INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('empty', 'occupied')),
            czas TEXT NOT NULL,
            numer_rejestracyjny TEXT
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

import time

# Słownik przechowujący ostatnie statusy dla każdego miejsca parkingowego
# Format: {place_id: [(status, timestamp), ...]}
recent_statuses = {}

# Funkcja zapisująca zmianę statusu, sprawdzająca stabilność zmiany
def save_parking_change(place_id, status, plate_number):
    """Zapisuje zmianę statusu miejsca parkingowego w bazie danych po weryfikacji stabilności statusu."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Pobierz ostatni zapisany status dla miejsca
    cursor.execute(
        "SELECT status FROM parking_status WHERE numer_miejsca = ? ORDER BY czas DESC LIMIT 1",
        (place_id,)
    )
    last_entry = cursor.fetchone()

    last_status = last_entry[0] if last_entry else None

    # Dodaj lub zaktualizuj status w historii statusów
    if place_id not in recent_statuses:
        recent_statuses[place_id] = []
    
    # Zapisz bieżący status i czas
    recent_statuses[place_id].append((status, time.time()))

    # Zachowaj tylko ostatnie 30 wpisów
    recent_statuses[place_id] = recent_statuses[place_id][-10:]

    # Sprawdzamy, czy status utrzymuje się przez określony czas
    consistent = True
    for state, _ in recent_statuses[place_id]:
        if state != status:
            consistent = False
            break
    
    if consistent:
        # Jeśli status jest spójny, zapisujemy go w bazie danych
        cursor.execute(
            "INSERT INTO parking_status (numer_miejsca, status, czas, numer_rejestracyjny) VALUES (?, ?, ?, ?)",
            (place_id, status, timestamp, plate_number if status == "occupied" else None)
        )
        conn.commit()

        # Logowanie zmiany statusu
        if last_status == "empty" and status == "occupied" and plate_number:
            log_event(f"Pojazd {plate_number} zajął miejsce {place_id}")

    conn.close()