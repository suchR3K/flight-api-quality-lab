# Wyniki testów manualnych

## MT-001: Dodanie i odczyt poprawnego lotu

Narzędzie: dokumentacja interaktywna /docs.

Dane:
- flight_number: "  LO789  "
- origin: WAW
- destination: FRA

Oczekiwany wynik:
- POST zwraca 201 i numer lotu bez otaczających spacji.
- GET z otrzymanym ID zwraca 200 i dane utworzonego lotu.

Wynik rzeczywisty:
- POST zwrócił 201.
- Numer lotu został zwrócony jako "LO789", bez otaczających spacji.
- GET zwrócił 200 i dane zgodne z utworzonym lotem.

Status: PASS.

## MT-002: Identyczne lotniska

Narzędzie: dokumentacja interaktywna /docs.

Dane:
- flight_number: LO999
- origin: WAW
- destination: WAW

Oczekiwany wynik:
- HTTP 422.
- Komunikat zawiera:
  "Origin and destination must be different".

Wynik rzeczywisty:
- POST zwrócił 422.
- Odpowiedź zawierała komunikat:
  "Origin and destination must be different".
- Żądanie zostało odrzucone zgodnie z wymaganiem.

Status: PASS.


## MT-003: Trwałość danych po odtworzeniu kontenera API

Środowisko:
- API i PostgreSQL uruchomione przez Docker Compose.

Kroki:
1. Utworzono lot przez POST /flights.
2. Pobrano lot przez GET /flights/{id}.
3. Odtworzono kontener API poleceniem:
   docker compose up -d --force-recreate --no-deps api
4. Ponownie pobrano ten sam lot, bez ponownego wykonywania POST.

Oczekiwany wynik:
- POST zwraca 201.
- GET przed odtworzeniem i po odtworzeniu zwraca 200.
- ID i dane lotu pozostają niezmienione.

Wynik rzeczywisty:
- POST zwrócił 201.
- Oba żądania GET zwróciły 200.
- ID i dane lotu pozostały niezmienione.

Status: PASS.

## MT-004: Użytkownik procesu aplikacji w kontenerze

Kroki:
1. Wykonano: docker compose exec api id

Oczekiwany wynik:
- Proces działa jako appuser z UID 10001, nie jako root.

Wynik rzeczywisty:
- uid=10001(appuser)
- gid=10001(appuser)

Status: PASS.
