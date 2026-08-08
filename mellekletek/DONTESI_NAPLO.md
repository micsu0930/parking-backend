# Döntési Napló és Reflexió

## 1. Döntési Napló (Decision Log Table)

| # | Döntési pont | Amit választottam | Miért | Milyen alternatívát vetettem el |
|---|---|---|---|---|
| **1** | **Backend Keretrendszer** | **Python + FastAPI** | Magas teljesítmény, típusbiztonság (Pydantic), és az OpenAPI/Swagger felület automatikus generálása. | **Java (Spring Boot):** Nehézkesebb boilerplate; **Express (Node.js):** Kézi Swagger konfigurációt igényelt volna. |
| **2** | **Adatbázis & Architektúra** | **PostgreSQL (Docker-ben) / SQLite (helyi teszteknél)** | Relációs felépítés garantálja az ACID tranzakciókat és az indexelt átfedés-ellenőrzést. | **MongoDB (NoSQL):** Az átfedések komplexebb és kevésbé hatékony szűrését tette volna lehetővé. |
| **3** | **Ütközés-ellenőrzés elhelyezése** | **Domain-rétegbeli guard a `crud.py`-ban** | Garantálja, hogy közvetlen modulhívás esetén sem alakulhat ki duplafoglalás semmilyen kódrészletből. | **Kizárólag API-szintű ellenőrzés:** Sérülékenyebb lett volna a háttérfolyamatok és tesztek felől. |
| **4** | **Foglalás lemondásának módja** | **Soft Delete (`status = CANCELLED`)** | Megőrzi az audit naplózást és a történeti adatokat az elemzésekhez. | **Hard Delete (`DELETE FROM` SQL):** Az adatok végleges elvesztésével járt volna. |
