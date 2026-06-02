# [GRUPI NIMI] — Eesti andmete maht, terviklikkus ja uuenemine Open Food Facts andmebaasis

## Äriküsimus

Kui hästi katab [Open Food Facts andmebaas](https://world.openfoodfacts.org/discover) Eesti turul müüdavaid toidutooteid ja kui terviklikud on nende andmed?

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
csv[OpenFoodFacts CSV snapshot] --> py[Python ingestion scripts]
airflow[Airflow scheduler] -->|"@daily"| txt[Delta index TXT]
txt --> jsonl[Daily delta JSONL files]
airflow -->|BashOperator| dbt[dbt run + dbt test]
jsonl --> py
py --> raw[(staging.raw_products)]
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
| OpenFoodFacts delta loend | TXT | Jah, iga päev | Andmestiku uuendamine |
| OpenFoodFacts päeva delta | JSONL | Jah/Ei (iga deltafail eraldi on staatiline, aga iga päev lisandub uus fail) | Andmestiku uuendamine |

## Stack

| Komponent | Tööriist |
|-----------|---------|
| Sissevõtt | Python, duckdb |
| Transformatsioon | dbt |
| Andmehoidla | PostgreSQL (pgDuckDB) |
| Näidikulaud | Apache Superset 6.x |
| Orkestreerimine | Airflow (TODO)|

## Saladused ja konfiguratsioon

Kõik paroolid ja võtmed on `.env` failis. Reposse läheb ainult `.env.example`. Päris `.env` on `.gitignore`-s.

| Muutuja | Tähendus |
|---------|----------|
| `POSTGRES_PASSWORD` | Analüütika andmebaasi parool |
| `SUPERSET_SECRET_KEY` | Superset'i sessiooniküpsiste krüptovõti — **genereeri uus**, ära jäta vaikeväärtust |
| `SUPERSET_ADMIN_USER` / `SUPERSET_ADMIN_PASSWORD` | Superset'i admin-kasutaja |

## Andmevoog lühidalt

1. **Sissevõtt** — OpenFoodFacts andmed saadakse veebist alla laaditud CSV snapshotist, millest filtreeritud Eesti andmed säilitatakse projektis Parquet-formaadis (`ee_products_bootstrap.parquet`) ning tulevikus ka OpenFoodFacts API deltafailidest. Python ingestion scriptid töötlevad andmed ja valmistavad need laadimiseks ette.

2. **Laadimine** — Andmed laaditakse PostgreSQL + pg_duckdb warehouse'i `raw.raw_products` tabelisse, kust dbt kasutab neid source layerina.

3. **Transformatsioon** — dbt mudelid puhastavad ja normaliseerivad andmed `staging` kihis (`staging.stg_products`), arvutavad mõõdikuid `intermediate` kihis ning loovad dashboard-ready marts tabelid (nt andmete terviklikkus ja toodete statistika).

4. **Testimine** — dbt testid kontrollivad võtmeväljade korrektsust, unikaalsust ja andmete terviklikkust. Planeeritud on nii schema-testid kui ka äriloogika kontrollid.

5. **Näidikulaud** — Apache Superset dashboardid visualiseerivad toodete statistikat, Nutri-Score jaotust, NOVA gruppe ning andmete terviklikkuse mõõdikuid.

## Andmekvaliteedi testid

Projekt kontrollib järgmist:

1. Test 1 - toote ID on unikaalne
2. Test 2 - toitained 100 g kohta jäävad vahemikku 0-100
3. Test 3 - suhkrute kogus pole suurem kui süsivesikute kogus, küllastunud rasvhapete kogus pole suurem kui rasvad kokku
4. Test 4 - koostisosade loetelu, pakendi tüüp ja tootekategoria pole arv või väga lühike sõne (<3 märki)
5. Test 5 - kogus on arv või arv, millele järgnevad sõned (ühik)

Testide tulemused: salvestatakse tabelisse `quality_checks_summary`  [/ kuidas vaadata]

## Projekti struktuur

```text
OFF-projekt/
├── .env.example              # Näidis-keskkonnamuutujad
├── .gitignore                # Gitist välistatud failid ja kaustad
├── .python-version           # Python versiooni definitsioon
├── Dockerfile                # Airflow/dbt custom image
├── Dockerfile.superset       # Superset custom image PostgreSQL driveriga
├── compose.yml               # Docker teenuste definitsioonid
├── pyproject.toml            # Python dependency management
├── uv.lock                   # Lukustatud Python dependency versioonid
├── README.md                 # Projekti dokumentatsioon
│
├── airflow/
│   └── dags/
│       └── .gitkeep          # Airflow DAG-ide kaust
│
├── data/
│   ├── bootstrap/
│   │   ├── bootstrap_metadata.json   # Bootstrap snapshot metadata
│   │   └── readme.md                 # Bootstrap andmete kirjeldus
│   │
│   ├── deltas/
│   │   └── .gitkeep          # Päevaste deltafailide hoidla
│   │
│   ├── snapshots/
│   │   └── .gitkeep          # Snapshot failide hoidla
│   │
│   └── state/
│       └── .gitkeep          # Pipeline state / checkpoint failid
│
├── dbt_project/
│   ├── dbt_project.yml       # dbt projekti põhikonfiguratsioon
│   ├── profiles.yml          # dbt analüütika andmebaasi ühendus
│   │
│   ├── macros/
│   │   ├── .gitkeep
│   │   └── generate_schema_name.sql  # Custom schema naming macro
│   │
│   ├── models/
│   │   ├── staging/
│   │   │   ├── .gitkeep
│   │   │   ├── sources.yml          # dbt allikad
│   │   │   └── stg_products.sql     # Staging mudelid, sh kvaliteedikontrollid
│   │   │
│   │   ├── intermediate/
│   │   │   └── .gitkeep             # Äriloogika ja mõõdikute mudelid
│   │   │
│   │   └── marts/
│   │       └── .gitkeep             # Näidikulaua sisendtabelid
│   │
│   └── seeds/
│       └── .gitkeep                 # dbt seed failid
│
├── docs/
│   ├── arhitektuur.md       # Süsteemi arhitektuuri kirjeldus
│   └── progress.md          # Sprintide ja arenduse progress
│
├── ingestion/
│   ├── .gitkeep
│   │
│   └── bootstrap/
│       ├── create_bootstrap_dataset.py  # Eesti toodete bootstrap dataset
│       ├── download_off_snapshot.py     # OFF snapshot allalaadimine
│       ├── filter_estonia_products.py   # Eesti toodete filtreerimine
│       ├── load_bootstrap_snapshot.py   # Bootstrap andmete laadimine warehouse'i
│       └── utils.py                     # Üldised ingest utiliidid
│
├── init/
│   ├── .gitkeep
│   ├── 01_create_schemas.sql   # Warehouse schema-de loomine
│   └── 02_extensions.sql       # PostgreSQL extensionite aktiveerimine
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
git clone https://github.com/karlraim/OFF-projekt.git
cd OFF-projekt
```

---

### 3. `.env` faili loomine

Kopeeri näidisfail:

```bash id="run2"
cp .env.example .env
```

Muuda vajadusel väärtused.

Olulisemad muutujad:

```env id="run3"
POSTGRES_USER=off-projekt
POSTGRES_PASSWORD=off-projekt
POSTGRES_DB=off-projekt

SUPERSET_SECRET_KEY=<genereeri_uus_secret_key>
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin
```

Superset secret key genereerimine:

```bash id="run4"
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 4. Bootstrap andmete loomine või uuendamine (valikuline)

Projektiga on juba kaasas bootstrap dataset seisuga **2026-05-20**, mis võimaldab:

* kiiret lokaalset arendust,
* demo keskkonda,
* offline testimist.

Olemasolev bootstrap:

```text id="run5"
data/bootstrap/ee_products_bootstrap.parquet
```

Seetõttu ei ole esmasel käivitamisel vaja OpenFoodFacts snapshotit uuesti alla laadida.

Kui soovitakse värskemaid andmeid, saab bootstrap datasetti uuendada:

```bash id="run6"
uv run python ingestion/bootstrap/create_bootstrap_dataset.py
```

Script:

1. laadib alla OpenFoodFacts täieliku snapshoti,
2. filtreerib välja Eesti tooted,
3. salvestab tulemuse Parquet-formaadis bootstrap datasetina.

Tulemus:

```text id="run7"
data/bootstrap/ee_products_bootstrap.parquet
```

---

### 5. Docker stacki käivitamine

```bash id="run8"
docker compose up -d --build
```

Käivitatavad teenused:

* PostgreSQL + pgDuckDB
* dbt container
* Apache Superset
* Superset init container

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

### 7. dbt transformatsioonid

Sisene dbt konteinerisse:

```bash id="run11"
docker exec -it off-dbt bash
```

Liigu projekti:

```bash id="run12"
cd /opt/project/dbt_project
```

Käivita dbt:

```bash id="run13"
dbt run --profiles-dir .
```

Tulemus:

* `staging.stg_products`
* tulevikus ka `intermediate` ja `marts` mudelid

---

### 8. Superset

Superset on kättesaadav:

```text id="run14"
http://localhost:8088
```

Admin kasutaja luuakse automaatselt `superset-init` teenuse kaudu.

---

### 9. PostgreSQL ühendamine Supersetiga

Superset GUI:

```text id="run15"
Settings → Database Connections → +
```

SQLAlchemy URI:

```text id="run16"
postgresql+psycopg2://off-projekt:off-projekt@analytics-db:5432/off-projekt
```

---

### 10. Näidis dashboard

Näidis dashboard export:

```text id="run17"
superset/dashboards/dashboard_export_20260528T130721.zip
```

Näidis screenshot:

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
