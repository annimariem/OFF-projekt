from pathlib import Path

import requests

from delta_metadata import (
    get_required_delta_files,
    mark_delta_as_downloaded,
)

DELTA_DOWNLOAD_DIR = Path("data/deltas/files")

HEADERS = {"User-Agent": "OFF-Estonia-Analytics/1.0"}


def download_delta_file(
    delta_id,
    delta_filename,
    source_url,
):
    """
    Laeb ühe deltafaili alla.
    """

    DELTA_DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = DELTA_DOWNLOAD_DIR / delta_filename

    if output_path.exists():

        print(f"Fail juba olemas: " f"{delta_filename}")

        mark_delta_as_downloaded(delta_id)

        return

    print(f"Laen deltafaili: " f"{delta_filename}")

    response = requests.get(
        source_url,
        stream=True,
        timeout=300,
        headers=HEADERS,
    )

    response.raise_for_status()

    with open(output_path, "wb") as f:

        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)

    mark_delta_as_downloaded(delta_id)

    print(f"Salvestatud: " f"{output_path}")


def download_new_deltas():
    """
    Laeb alla kõik vajalikud deltad.

    Vajalik = delta on:
      - uuem kui viimane bootstrap
      - veel alla laadimata
    """

    pending_deltas = get_required_delta_files()

    if not pending_deltas:

        print("Allalaadimist vajavaid " "deltafaile ei leitud.")

        return

    print(f"Leitud " f"{len(pending_deltas)} " f"allalaaditavat deltafaili.")

    for delta in pending_deltas:

        download_delta_file(
            delta_id=delta["delta_id"],
            delta_filename=(delta["delta_filename"]),
            source_url=(delta["source_url"]),
        )

    print()

    print("Deltafailide " "allalaadimine lõpetatud.")


if __name__ == "__main__":
    download_new_deltas()
