from pathlib import Path

import requests

DELTA_INDEX_URL = "https://static.openfoodfacts.org/data/delta/index.txt"

DELTA_INDEX_PATH = Path("data/deltas/index.txt")

HEADERS = {"User-Agent": "OFF-Estonia-Analytics/1.0"}


def download_delta_index():

    print(f"Laadin delta indexi: " f"{DELTA_INDEX_URL}")

    response = requests.get(
        DELTA_INDEX_URL,
        headers=HEADERS,
        timeout=60,
    )

    response.raise_for_status()

    DELTA_INDEX_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    DELTA_INDEX_PATH.write_text(
        response.text,
        encoding="utf-8",
    )

    print(f"Delta index salvestatud: " f"{DELTA_INDEX_PATH}")


if __name__ == "__main__":
    download_delta_index()
