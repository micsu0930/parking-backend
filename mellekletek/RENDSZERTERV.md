# Rendszerterv

## 1. Rendszer áttekintése
A rendszer egy microservice, REST API alapú parkolóhely foglalásó backend szolgáltatás. A program fő célja a parkolóhelyek nyomon követése, a foglalások felvétele és kezelése, valamint a dupla foglalások megbízható megelőzése.

---

## 2. Architektúra és Technológiai Stakk

A rendszer Layered Architecture felépítést követ, elválasztva az API interfészt, az üzleti logikát és az adatbázis-kezelést:

- **Nyelv és keretrendszer:** Python 3.12 + FastAPI (Magas teljesítmény, automatikus OpenAPI/Swagger dokumentáció)
- **Adatbázis & ORM:** PostgreSQL 16 + SQLAlchemy 2.0 (Relációs adatmodell, tranzakciókezelés, indexelt lekérdezések)
- **Adatvalidáció:** Pydantic v2 (Típusbiztonság, dátum- és e-mail szűrés)
- **Konténerizáció:** Docker & Docker Compose (Egy parancssoros `docker compose up` indítás)
- **Tesztelés:** Pytest + HTTPX (Mértékadó unit- és integrációs tesztszoftver)

---

## 3. Entitás-Kapcsolat Diagram (ER Diagram)

Az alábbi diagram az adatbázis entitásait és azok relációit mutatja be:

```mermaid
erDiagram
    PARKING_SPOTS ||--o{ RESERVATIONS : "has many"
    
    PARKING_SPOTS {
        int id PK "Primary Key"
        string spot_number UK "Unique, Indexed"
        enum spot_type "STANDARD, EV, HANDICAPPED, VIP"
        boolean is_active "Default: True"
    }
    
    RESERVATIONS {
        int id PK "Primary Key"
        int spot_id FK "Foreign Key, Indexed"
        string requester_name
        string requester_email
        datetime start_time "UTC, Indexed"
        datetime end_time "UTC, Indexed"
        enum status "ACTIVE, CANCELLED"
        datetime created_at "UTC Timestamp"
    }
```

---

## 4. Átfedés ellenőrzési Algoritmus 

A rendszer legkritikusabb üzleti logikája a duplafoglalások megelőzése. Két időtartam $[A_{kezd}, A_{vég}]$ és $[B_{kezd}, B_{vég}]$ akkor és csak akkor fedi át egymást, ha:

$$\text{új\_kezdett} < \text{létező\_vég} \quad \text{ÉS} \quad \text{új\_vég} > \text{létező\_kezdett}$$

A szűrés kizárólag az `ACTIVE` státuszú foglalásokat veszi figyelembe. Amennyiben ütközés áll fenn, a rendszer elutasítja a kérést (`HTTP 409 Conflict` / `HTTP 400 Bad Request`).

---

## 5. Folyamat diagram

Az alábbi folyamatábra bemutatja egy új foglalási kérés feldolgozási lépéseit és az áttfedés ellenőrzést:

```mermaid
sequenceDiagram
    autonumber
    actor Client as Kliens / Felhasználó
    participant API as FastAPI Router (main.py)
    participant CRUD as Business Logic (crud.py)
    participant DB as PostgreSQL Adatbázis

    Client->>API: POST /reservations (JSON)
    API->>CRUD: get_spot_by_id(spot_id)
    CRUD->>DB: SELECT * FROM parking_spots WHERE id = spot_id
    DB-->>CRUD: Parkolóhely adatai
    
    alt Parkolóhely Nem Létezik
        CRUD-->>API: None
        API-->>Client: HTTP 404 Not Found
    else Parkolóhely Létezik
        API->>CRUD: create_reservation(start_time, end_time)
        CRUD->>CRUD: check_time_overlap(spot_id, start, end)
        CRUD->>DB: SELECT * FROM reservations WHERE spot_id AND ACTIVE AND overlap
        DB-->>CRUD: Találatok száma
        
        alt Ütközés Áll Fenn (Overlap == True)
            CRUD-->>API: ValueError ("Already reserved")
            API-->>Client: HTTP 409 Conflict / 400 Bad Request
        else Nincs Ütközés (Overlap == False)
            CRUD->>DB: INSERT INTO reservations (...)
            DB-->>CRUD: Új Reservation rekord (id-val)
            CRUD-->>API: Reservation objektum
            API-->>Client: HTTP 201 Created (JSON)
        end
    end
```