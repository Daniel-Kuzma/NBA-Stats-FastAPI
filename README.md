# NBA Stats API 

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)

REST API służące do pobierania, analizowania i zarządzania statystykami zawodników oraz drużyn NBA. System automatycznie integruje się z zewnętrznymi źródłami danych (NBA API), agregując logi meczowe i udostępniając je w ujednoliconej formie. 
Projekt został zbudowany jako wizytówka do portfolio z naciskiem na najlepsze praktyki backendowe: bezpieczeństwo (JWT, Rate Limiting), separację warstw dostępu (UUID dla klientów publicznych, Integer dla relacji wewnętrznych) oraz wysoką wydajność.

## Główne funkcjonalności

* **Autoryzacja i Bezpieczeństwo:** Rejestracja, logowanie oraz ochrona endpointów przy użyciu tokenów JWT.
* **Zarządzanie Użytkownikami:** Panel administratora do zmiany statusów i ról użytkowników, a także usuwania kont.
* **Zarządzanie przepływem danych:** Z panelu admina można pobierać nowe dane, a także weryfikować w logach systemowych, jaki rodzaj i jaka ilość informacji została pobrana.
* **Ulubieni Zawodnicy i Drużyny:** Relacyjna baza danych pozwalająca użytkownikom śledzić statystyki wybranych graczy i drużyn.
* **Statystyki:** Przeglądanie statystyk drużyn i zawodników. Dodatkowo możliwość analizy bezpośrednich starć (jak gracz lub drużyna radzi sobie przeciwko konkretnemu rywalowi).
* **Ochrona przed nadużyciami:** Wdrożony `SlowAPI` (Tiered Rate Limiting) chroniący krytyczne endpointy przed atakami Brute Force i DDoS.
* **Harmonogram:** Funkcje wywoływane automatycznie co godzinę pobierają nowe dane meczowe oraz logi graczy i drużyn (system samoczynnie aktualizuje przynależność klubową zawodników w przypadku transferów).

## Stack Technologiczny

* **Backend Framework:** FastAPI
* **Baza Danych ORM:** SQLAlchemy (z bazą SQLite do testów)
* **Zarządzanie Środowiskiem:** Pydantic Settings
* **Bezpieczeństwo:** Passlib (Bcrypt), PyJWT, SlowAPI
* **Testowanie:** Pytest, Pytest-Asyncio, HTTPX

## Instalacja i Uruchomienie (Lokalnie)

### 1. Pobierz biblioteki i skonfiguruj zmienne środowiskowe
Zainstaluj wymagane pakiety:
`pip install -r requirements.txt`
Utwórz plik .env w głównym katalogu projektu, bazując na pliku przykładowym:
`cp .env.example .env`

### 2. Utwórz bazę danych
Wykonaj migrację Alembic, aby zbudować strukturę tabel:
`alembic upgrade "b00597db2665"`

### 3. Uruchom serwer
`fastapi run main.py`
Aplikacja będzie dostępna pod adresem: http://127.0.0.1:8000

### 4. Utwórz konto admina
Podczas tworzenia konta w endpoincie /sign-in/create_user w schemacie JSON należy ręcznie zmienić `"role": "user"` na `"role": "admin"`. Po zalogowaniu na to konto uzyskasz dostęp do panelu administratora.
(Uwaga: Jest to uproszczenie na potrzeby środowiska deweloperskiego/testowego w wersji końcowej było by to zmienione).

### 5. Załadowanie danych historycznych
Po utworzeniu konta administratora, przy pierwszym uruchomieniu aplikacji należy zainicjować bazę danymi z przeszłości. Wywołaj endpoint `/admin/load_historical_data`. Po jego poprawnym wykonaniu, aplikacja jest w pełni gotowa do pracy.

## Uruchomienie testów
Projekt posiada pełne pokrycie testami dla głównych ścieżek autoryzacji, operacji CRUD i mechanizmów chroniących aplikację. Aby uruchomić testy integracyjne w wyizolowanym środowisku pamięci, wpisz w konsoli:
`pytest`

## Dokumentacja API
Po uruchomieniu aplikacji, FastAPI automatycznie generuje interaktywną dokumentację. Możesz ją znaleźć pod adresami:
Swagger UI: `http://127.0.0.1:8000/docs`
ReDoc: `http://127.0.0.1:8000/redoc`

## Struktura projektu
```text
nba-stats-api/
├── core/                   # Konfiguracja (Settings, Security, Limiter)
├── models/                 # Modele bazodanowe SQLAlchemy (Users, Players, itp.)
├── routes/                 # Endpointy (Routery dla Auth, Users, Admin)
├── test/                   # Testy integracyjne (Pytest)
├── .env.example            # Szablon zmiennych środowiskowych
├── database.py             # Połączenie z bazą danych (AsyncEngine)
├── main.py                 # Punkt wejścia aplikacji FastAPI
└── requirements.txt        # Zależności projektu
```
