from pathlib import Path

from delta_metadata import (
    register_delta_file,
)

DELTA_INDEX_PATH = Path("data/deltas/index.txt")

DELTA_BASE_URL = "https://static.openfoodfacts.org/data/delta/"


def register_delta_files():
    """
    Registreerib kõik index.txt failis leiduvad
    deltafailid metadata tabelisse.
    """

    if not DELTA_INDEX_PATH.exists():

        raise FileNotFoundError(f"Delta index puudub: " f"{DELTA_INDEX_PATH}")

    with open(
        DELTA_INDEX_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        delta_filenames = [line.strip() for line in f if line.strip()]

    total_count = len(delta_filenames)

    registered_count = 0

    skipped_count = 0

    for delta_filename in delta_filenames:

        source_url = DELTA_BASE_URL + delta_filename

        delta_id = register_delta_file(
            delta_filename=delta_filename,
            source_url=source_url,
        )

        if delta_id is None:

            skipped_count += 1

        else:

            registered_count += 1

    print()

    print(f"Deltafaile indexis: " f"{total_count}")

    print(f"Uusi deltafaile registreeritud: " f"{registered_count}")

    print(f"Juba registris: " f"{skipped_count}")


if __name__ == "__main__":
    register_delta_files()
