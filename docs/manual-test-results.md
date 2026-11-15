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
