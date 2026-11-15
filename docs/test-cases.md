# Flight API - przypadki testowe

## TC-001: Pobranie istniejacego lotu

Warunki wstepne:
- Aplikacja zawiera lot o ID 1:
  - flight_number: LO123
  - origin: WAW
  - destination: LHR

Kroki:
1. Wyslij zadanie GET /flights/1.

Oczekiwany wynik:
- Kod HTTP: 200.
- Odpowiedz jest w formacie JSON.
- Pole id ma wartosc 1.
- Pole flight_number ma wartosc LO123.
- Pole origin ma wartosc WAW.
- Pole destination ma wartosc LHR.

Status wykonania: jeszcze niewykonany.
