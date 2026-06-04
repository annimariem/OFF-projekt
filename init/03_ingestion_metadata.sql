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

    -- Delta avaldamise aeg (kui allikas selle annab).
    published_at TIMESTAMPTZ,

    -- Millal pipeline delta avastas.
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Millal delta tegelikult alla laaditi.
    downloaded_at TIMESTAMPTZ
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