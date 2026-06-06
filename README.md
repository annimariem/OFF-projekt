# OpenFoodFacts Eesti toodete andmeplatvorm

## Äriküsimus

Kas [OpenFoodFacts](https://openfoodfacts.github.io/) andmebaas sisaldab piisavalt kvaliteetseid Eesti toodete andmeid, et neid kasutada analüütikas, teadustöös või avaliku toiduinfo rakendustes?

Open Food Facts on avalik, vabatahtlike poolt täiendatav andmebaas, mis koondab rohkem kui nelja miljoni toidu pakendiandmeid 150 riigist. Andmebaasi on võimalik kasutada näiteks rakenduste loomiseks ja teadustöö sisendina.

**Mõõdikud:**

1. Eestis müüdavate toodete koguarv andmebaasis
2. Lisanduvate toodete arv päevas
3. Andmete terviklikkus: toodete arv/osakaal, millel on olemas:
   1) energia ja peamiste toitainete sisaldus,
   2) koostisosade nimekiri,
   3) pakendi materjal,
   4) kogus (netomass/ruumala vmt).

Võimalusel arvutame mõõdikud ka tootekategooriate lõikes.


## Arhitektuur
```mermaid
flowchart TD
csv[OpenFoodFacts CSV snapshot] --> parquet[Bootstrap Parquet dataset]
parquet --> py[Python ingestion scripts]

airflow[Airflow scheduler] -->|"BashOperator@daily"| txt[Download delta index]
txt -->|BashOperator| reg[Register delta files]
reg -->|BashOperator| jsonl[Download daily delta JSONL files]
jsonl -->|BashOperator| proc[Process delta files]
proc -->|BashOperator| dbt[dbt run + dbt test]

py --> raw[(raw.raw_products)]
proc --> raw

raw -->|dbt staging| stg[staging.stg_products]
stg -->|dbt intermediate| int[intermediate.int_product_metrics]

int -->|dbt marts| mart1[(marts.mart_product_growth)]
int -->|dbt marts| mart2[(marts.mart_data_completeness)]

mart1 --> dashboard[Superset dashboard]
mart2 --> dashboard
```
Täpsem kirjeldus: [`docs/arhitektuur.md`](docs/arhitektuur.md)



## Andmestik

| Allikas | Tüüp | Ajas muutuv? | Roll |
|---------|------|--------------|------|
| OpenFoodFacts andmebaas | CSV| Jah, iga päev | Algne andmestiku laadimine |
| Bootstrap dataset | Parquet | Jah/Ei (kasutaja poolt uuendatav) | Arendus- ja testkeskkond |
| OpenFoodFacts delta loend | TXT | Jah, iga päev | Andmestiku uuendamine |
| OpenFoodFacts päeva delta | JSONL | Jah/Ei (iga deltafail eraldi on staatiline, aga iga päev lisandub uus fail) | Andmestiku uuendamine |

## Stack

| Komponent | Tööriist |
|-----------|---------|
| Sissevõtt | Python, duckdb |
| Andmehoidla | PostgreSQL (pgDuckDB) |
| Transformatsioonid | dbt |
| Näidikulaud | Apache Superset 6.x |
| Orkestreerimine | Apache Airflow |

## Saladused ja konfiguratsioon

Kõik paroolid ja võtmed on `.env` failis. Reposse läheb ainult `.env.example`. Päris `.env` on `.gitignore`-s.

## Andmevoog lühidalt

1. Bootstrap dataset laaditakse PostgreSQL andmebaasi.
2. Airflow DAG kontrollib regulaarselt OpenFoodFacts deltaindeksit.
3. Uued deltafailid registreeritakse ja töödeldakse.
4. Muudatused viiakse toorandmete tabelisse.
5. dbt ehitab staging, intermediate ja marts kihid.
6. dbt testid kontrollivad andmekvaliteeti.
7. Superset visualiseerib marts-kihi andmeid.


## Andmekvaliteedi testid

Andmekvaliteeti kontrollitakse `dbt` testide kaudu. Kuna Open Food Facts andmed on sisestatud vabatahtlike poolt ja sisaldavad tihti vigu, kasutame ebakorrektsete kirjete tuvastamiseks `severity: warn` taset, mis võimaldab pipeline'il jätkata, kuid teavitab vigastest andmetest.

1. **`staging.stg_products`** — `product_code` on unikaalne ja täidetud (andmete terviklikkuse kontroll).
2. **`staging.stg_products`** — toitainete sisaldus (rasvad, süsivesikud, valgud jm) jääb vahemikku 0–100g.
3. **`staging.stg_products`** — suhkru sisaldus ≤ süsivesikute koguarv ja küllastunud rasvhapped ≤ rasvad kokku.
4. **`staging.stg_products`** — `categories_en` pikkus on vähemalt 3 märki ja ei koosne ainult numbritest (tehnilise prügi filtreerimine tekstiväljadest).
5. **`staging.stg_products`** — `quantity` väli algab numbriga (formaadi kontroll, et tagada andmete loetavus).
6. **`intermediate.int_product_metrics`** — `completeness_score` on vahemikus 0–4 (mõõdiku arvutuse korrektsuse kontroll).
7. **`intermediate.int_product_metrics`** — tooteinfo olemasolu näitajad (nt kas toitumisteave või koostisosad on kirjas) on alati täidetud (arvutusloogika kontroll).
8. **`marts.mart_data_completeness`** — koondstatistika (toodete koguarv, unikaalsete sisestajate arv) on alati positiivne arv ega ole tühi (raporti usaldusväärsuse kontroll).


dbt testid käivitatakse automaatselt Airflow pipeline lõpus. Tulemused on nähtavad DAG-i logides. Teste on võimalik ka käsitsi käivitada.

## dbt käsud (käsitsi käivitamiseks)

```bash
docker exec -it off-dbt bash

# dbt projekti kaustas:
cd /opt/project/dbt_project

dbt run --profiles-dir .                  # käivitab kõik mudelid
dbt test --profiles-dir .                 # käivitab kõik testid

dbt test --select stg_products            # käivitab ainult stage testid
dbt test --select int_product_metrics     # käivitab ainult intermediate testid
dbt test --select mart_data_completeness  # käivitab ainult mart testid
```


## Projekti struktuur

```text
OFF-projekt/
├── .env.example              # Näidis-keskkonnamuutujad
├── .gitignore                # Gitist välistatud failid ja kaustad
├── .python-version           # Python versiooni definitsioon
├── Dockerfile.airflow        # Airflow/dbt custom image
├── Dockerfile.superset       # Superset custom image PostgreSQL driveriga
├── compose.yml               # Docker teenuste definitsioonid
├── pyproject.toml            # Python dependency management
├── uv.lock                   # Lukustatud Python dependency versioonid
├── README.md                 # Projekti dokumentatsioon
│
├── airflow/
│   └── dags/
│       └── off_pipeline.py   # Põhi-DAG
│
├── data/
│   ├── bootstrap/
│   │   ├── bootstrap_metadata.json   # Bootstrap snapshot metadata
│   │   └── readme.md                 # Bootstrap andmete kirjeldus
│   │
│   ├── deltas/
│   │   └── .gitkeep          # Päevaste deltafailide hoidla
│   │
│   └── snapshots/
│       └── .gitkeep          # Snapshot failide hoidla
│
├── dbt_project/
│   ├── dbt_project.yml       # dbt projekti põhikonfiguratsioon
│   ├── profiles.yml          # dbt analüütika andmebaasi ühendus
│   │
│   ├── macros/
│   │   └── generate_schema_name.sql  # Custom schema naming macro
│   │
│   ├── models/
│   │   ├── staging/          # Staging mudelid
│   │   ├── intermediate/     # Äriloogika ja mõõdikute mudelid
│   │   └── marts/            # Näidikulaua sisendtabelid
│
├── docs/
│   ├── arhitektuur.md       # Süsteemi arhitektuuri kirjeldus
│   └── progress.md          # Sprintide ja arenduse progress
│
├── ingestion/
│   │── bootstrap/
│   │   ├── bootstrap_metadata.py        # Bootstrap metadata kirjutamine
│   │   ├── create_bootstrap_dataset.py  # Eesti toodete bootstrap dataset
│   │   ├── download_off_snapshot.py     # OFF snapshot allalaadimine
│   │   ├── filter_estonia_products.py   # Eesti toodete filtreerimine
│   │   └── load_bootstrap_snapshot.py   # Bootstrap andmete laadimine warehouse'i
│   │
│   └── deltas/
│       ├── delta_metadata.py            # Deltafailide metadata kirjutamine
│       ├── download_delta_index.py      # Deltaindeksi allalaadimine
│       ├── download_new_deltas.py       # Registreeritud deltafailide allalaadimine
│       ├── load_delta_file.py           # Ühe deltafaili laadimine warehouse'i
│       ├── process_delta_file.py        # Deltafailide töötlemine
│       └── register_delta_files.py      # Uute deltafailide registreerimine
├── init/
│   ├── 01_create_schemas.sql      # Warehouse schema-de loomine
│   ├── 02_extensions.sql          # PostgreSQL extensionite aktiveerimine
│   └── 03_ingestion_metadata.sql  # Metadata tabelite loomine
│
└── superset/
    ├── init_superset.sh        # Superset init
    ├── superset_config.py      # Superset konfiguratsioon
    │
    └── dashboards/
        ├── dashboard_export_20260528T130721.zip
        │                           # Näidikulaua näite export
        │
        └── open-food-facts-eesti-andmed-2026-05-28T13-08-17.526Z.jpg
                                    # Näidikulaua pilt
```


## Käivitamine

### 1. Eeldused

Projekt eeldab:

* Docker Desktop või Docker Engine
* Docker Compose
* vähemalt ~10 GB vaba kettaruumi snapshoti töötlemiseks

Soovituslikud tööriistad:

* DBeaver
* VSCode
* Python 3.12 + `uv`

---

### 2. Repositooriumi kloonimine

```bash id="run1"
git clone https://github.com/maarja-k/OFF-projekt
cd OFF-projekt
```

---

### 3. `.env` faili loomine

Kopeeri näidisfail:

```bash id="run2"
cp .env.example .env
```

Muuda vajadusel väärtused.

Superset secret key genereerimine:
```bash id="run4"
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 4. Bootstrap andmete loomine või uuendamine (valikuline)

Projektiga on juba kaasas bootstrap dataset seisuga **2026-05-28**, mis võimaldab:

* kiiret lokaalset arendust,
* demo keskkonda,
* offline testimist.

Kaasasolev bootstrap:

```text id="run5"
data/bootstrap/ee_products_bootstrap.parquet
```

Seetõttu ei ole esmasel käivitamisel vaja OpenFoodFacts snapshotit uuesti alla laadida.

Kui soovitakse värskemaid andmeid, saab bootstrap datasetti uuendada:

```bash id="run6"
uv run python ingestion/bootstrap/create_bootstrap_dataset.py
```

Skript:

1. laadib alla OpenFoodFacts täieliku snapshoti,
2. filtreerib välja Eesti tooted,
3. salvestab tulemuse Parquet-formaadis bootstrap datasetina.

---

### 5. Docker stacki käivitamine

```bash id="run8"
docker compose up -d --build
```

Käivitatavad teenused:

* PostgreSQL + pgDuckDB
* Apache Airflow
* Apache Superset
* Superset init container

Kontrolli teenuste olekut:

```bash
docker compose ps
```

Kõik teenused peaksid olema olekus:

```text
running
```

Pärast esmakordset käivitamist on kättesaadavad järgmised veebiliidesed:

| Teenus | URL |
|---------|---------|
| Airflow | http://localhost:8080 |
| Superset | http://localhost:8088 |

Pordid sõltuvad .env muutujatest.

---

### 6. Bootstrap andmete laadimine warehouse'i

```bash id="run9"
uv run python ingestion/bootstrap/load_bootstrap_snapshot.py
```

Andmed laaditakse tabelisse:

```text id="run10"
raw.raw_products
```

---

### 7. Airflow veebiliides

```text
http://localhost:8080
```

Kasutajanimi ja parool määratakse `.env` failis:

```env
AIRFLOW_USER=admin
AIRFLOW_PASSWORD=admin
```

### 8. Käivita DAG esmakordselt

Airflow UI:

```text
DAGs → off_pipeline → Trigger DAG
```

või käsurealt:

```bash
docker exec -it off-airflow airflow dags trigger off_pipeline
```

---

### 9. Superset veebiliides

Superset on kättesaadav:

```text id="run14"
http://localhost:8088
```

Admin kasutaja luuakse automaatselt `superset-init` teenuse kaudu.

---

### 10. PostgreSQL ühendamine Supersetiga

Superset GUI:

```text id="run15"
Settings → Database Connections → +
```

SQLAlchemy URI:

```text id="run16"
postgresql+psycopg2://off-projekt:off-projekt@analytics-db:5432/off-projekt
```
Näites kasutatakse vaikimisi .env.example väärtusi.

---

### 11. Näidikulaud

Näidikulaua export:

```text id="run17"
superset/dashboards/dashboard_export_20260528T130721.zip
```

Näidikulaua screenshot:

```text id="run18"
superset/dashboards/open-food-facts-eesti-andmed-2026-05-28T13-08-17.526Z.jpg
```


## Kokkuvõte, puudused ja võimalikud edasiarendused

**Kokkuvõte:**
- [Loetle, mis on lõpule viidud, mis töötab hästi]

**Puudused:**
- [Loetle ausalt, mis jäi tegemata - see ei mõjuta hinnet negatiivselt, vaid aitab hinnata]

**Mis edasi:**
- [Mida tahaksid edasi teha, kui aega oleks rohkem]

## Meeskond

| Roll | Vastutus | Täitja |
|------|----------|--------|
| Andmeallika omanik | Kirjutab sissevõtu ja puhastamise loogika, häälestab Airflow DAG-id | Karl Räim |
| Transformatsioonide omanik | Kirjutab intermediate/marts kihi mudelid ja mõõdikute arvutuse | Maarja Kukk |
| Kvaliteedi omanik | Kirjutab testid ja vaatab läbi ebaõnnestunud kontrollid | Maarja Kukk, Anni Marie Maripuu |
| Näidikulaua omanik | Ehitab näidikulaua ja seob selle äriküsimusega | Anni Marie Maripuu, Marge Saamel |