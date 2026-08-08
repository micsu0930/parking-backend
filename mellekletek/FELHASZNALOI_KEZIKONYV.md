# Felhasználói Kézikönyv és API Leírás

## 1. Gyorsútmutató (Indítás Docker Compose-zal)

A teljes rendszer (adatbázissal és inicializált adatokkal együtt) egyetlen parancssorral indítható:


docker compose up --build


Az indítást követően a szolgáltatások az alábbi címeken érhetőek el:
- **Interaktív Swagger API Dokumentáció:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Dokumentáció:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 2. API Végpontok Leírása

### 2.1 Parkolóhelyek lekérdezése
- **HTTP Metódus:** `GET /spots`
- **Leírás:** Visszaadja a rendszerben létező aktív parkolóhelyeket.
- **Válasz példa (200 OK):**
```json
[
  {
    "id": 1,
    "spot_number": "A-101",
    "spot_type": "STANDARD",
    "is_active": true
  },
  {
    "id": 4,
    "spot_number": "B-201",
    "spot_type": "EV_CHARGING",
    "is_active": true
  }
]
```

### 2.2 Új foglalás létrehozása
- **HTTP Metódus:** `POST /reservations`
- **Kérés törzs (JSON):**
```json
{
  "spot_id": 1,
  "requester_name": "Kovács Péter",
  "requester_email": "peter@example.com",
  "start_time": "2026-08-08T10:00:00Z",
  "end_time": "2026-08-08T12:00:00Z"
}
```
- **Sikeres válasz (201 Created):**
```json
{
  "id": 1,
  "spot_id": 1,
  "requester_name": "Kovács Péter",
  "requester_email": "peter@example.com",
  "start_time": "2026-08-08T10:00:00Z",
  "end_time": "2026-08-08T12:00:00Z",
  "status": "ACTIVE",
  "created_at": "2026-08-08T06:00:00Z"
}
```
- **Hiba válasz (409 Conflict / 400 Bad Request):** Amennyiben az adott parkolóhely a megadott időszakban már foglalt.

### 2.3 Adott parkolóhely foglalásainak lekérdezése
- **HTTP Metódus:** `GET /spots/{spot_id}/reservations`
- **Leírás:** Lekérdezi az adott parkolóhelyhez tartozó aktív foglalásokat időrendi sorrendben.

### 2.4 Foglalás lemondása
- **HTTP Metódus:** `PATCH /reservations/{reservation_id}/cancel`
- **Leírás:** Lemondja a megadott azonosítójú foglalást (a státuszát `CANCELLED`-re állítja).

---

## 3. Automated Testek Futtatása

A tesztszoftver futtatásához használja a Pytest-et:


uv run pytest -v
