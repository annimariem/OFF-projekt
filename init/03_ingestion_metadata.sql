-- Bootstrap datasetide register --
-----------------------------------
-- Iga kirje kirjeldab ühte loodud bootstrap datasetti.
-- Bootstrap on EESTI toodete hetkeseis, mis on genereeritud
-- OpenFoodFactsi täielikust snapshotist.

CREATE TABLE IF NOT EXISTS raw.bootstrap_snapshots (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- OpenFoodFactsi algse snapshoti kuupäev.
    -- Seda kasutatakse bootstrapi värskuse hindamiseks.
    source_snapshot_date DATE NOT NULL,

    -- Millal bootstrap dataset genereeriti.
    bootstrap_created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Bootstrap parquet faili nimi või asukoht.
    bootstrap_file TEXT NOT NULL,

    -- Bootstrap datasetis olevate toodete arv.
    product_count INTEGER NOT NULL,

    -- Loomise tulemus:
    -- SUCCESS | FAILED
    status TEXT NOT NULL,

    -- Täiendavad märkused või veakirjeldused.
    notes TEXT
);

-- Projektiga kaasasoleva boostrapi kirje --
-- Allalaadimise kuupäev 2026-05-28, kirjete arv 5714.
INSERT INTO raw.bootstrap_snapshots (
    source_snapshot_date,
    bootstrap_file,
    product_count,
    status,
    notes
)
VALUES (
    DATE '2026-05-28',
    'data/bootstrap/ee_products_bootstrap.parquet',
    5714,
    'SUCCESS',
    'Initial bootstrap dataset committed with repository'
);

-- Bootstrap laadimiste ajalugu.
--
-- Iga kirje kirjeldab ühte bootstrap dataseti laadimist
-- raw.raw_products tabelisse.

CREATE TABLE IF NOT EXISTS raw.bootstrap_load_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Viide bootstrap datasetile, mida laaditi.
    snapshot_id BIGINT NOT NULL
        REFERENCES raw.bootstrap_snapshots(snapshot_id),

    -- Laadimise algus.
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Laadimise lõpp.
    finished_at TIMESTAMPTZ,

    -- Käivituse tulemus:
    -- SUCCESS | FAILED
    status TEXT NOT NULL,

    -- Eduka laadimise korral laaditud ridade arv.
    rows_loaded INTEGER,

    -- Veateade ebaõnnestumise korral.
    error_message TEXT
);

-- OpenFoodFactsi deltafailide register --
------------------------------------------
-- Tabel sisaldab kõiki avastatud deltafaile sõltumata sellest,
-- kas need on juba alla laaditud või töödeldud.

CREATE TABLE IF NOT EXISTS raw.delta_files (
    delta_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Delta faili nimi.
    delta_filename TEXT NOT NULL UNIQUE,

    -- Delta faili allalaadimise URL.
    source_url TEXT NOT NULL,

    -- Delta faili algushetk (Unix timestamp failinimest).
    delta_start_ts BIGINT NOT NULL,

    -- Delta faili lõpphetk (Unix timestamp failinimest).
    delta_end_ts BIGINT NOT NULL,

    -- Delta faili algushetk UTC kuupäeva/kellaajana.
    delta_start_datetime TIMESTAMPTZ NOT NULL,

    -- Delta faili lõpphetk UTC kuupäeva/kellaajana.
    delta_end_datetime TIMESTAMPTZ NOT NULL,

    -- Millal pipeline delta avastas.
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Millal delta alla laaditi.
    downloaded_at TIMESTAMPTZ,

    -- Filtreerimise käigus leitud Eesti toodete arv.
    filtered_product_count INTEGER,

    -- Raw kihti edukalt laaditud toodete arv.
    loaded_product_count INTEGER,

    -- Millal delta täielikult töödeldi.
    processed_at TIMESTAMPTZ
);


-- Deltafailide töötlemise ajalugu --
-------------------------------------
-- Üks deltafail võib teoreetiliselt olla töödeldud mitu korda,
-- seetõttu hoitakse töötlemise logi eraldi tabelis.

CREATE TABLE IF NOT EXISTS raw.delta_ingestion_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Töödeldud deltafail.
    delta_id BIGINT NOT NULL
        REFERENCES raw.delta_files(delta_id),

    -- Töötlemise algus.
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Töötlemise lõpp.
    finished_at TIMESTAMPTZ,

    -- Käivituse tulemus:
    -- SUCCESS | FAILED
    status TEXT NOT NULL,

    -- Töödeldud kirjete arv.
    rows_processed INTEGER,

    -- Veateade ebaõnnestumise korral.
    error_message TEXT
);