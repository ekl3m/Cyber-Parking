import time
import psutil
import os

from enum import Enum

# Lista logów przechowywana w pamięci
log_history = []

# Dodawanie wiadomości do listy logów
def log_event(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    log_history.append(log_message)
    print(log_message)

# Debug - funkcja do logowania zuzycia pamieci
def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    log_event(f"Zużycie pamięci: RSS={mem_info.rss // 1024} KB, VMS={mem_info.vms // 1024} KB")

# Enum, który umozliwia kontrole nad bramkami
class GateAction(Enum):
    ENTRY_OPEN = "Bramka wjazdowa się otwiera."
    ENTRY_CLOSE = "Bramka wjazdowa się zamyka."
    EXIT_OPEN = "Bramka wyjazdowa się otwiera."
    EXIT_CLOSE = "Bramka wyjazdowa się zamyka."

# Funkcja, ktora zajmuje sie obsluga bramek
def manage_gates(action: GateAction):
    if isinstance(action, GateAction):
        log_event(action.value)
    else:
        raise ValueError("Niepoprawna akcja dla bramki")