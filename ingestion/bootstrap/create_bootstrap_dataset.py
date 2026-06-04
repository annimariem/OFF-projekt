from pathlib import Path
from datetime import datetime, UTC

from download_off_snapshot import (
    download_snapshot,
    load_metadata,
)

from filter_estonia_products import (
    filter_estonia_products,
)

from bootstrap_metadata import (
    get_latest_bootstrap_snapshot,
    register_bootstrap_snapshot,
)

BOOTSTRAP_PATH = Path("data/bootstrap/ee_products_bootstrap.parquet")

BOOTSTRAP_MAX_AGE_DAYS = 14


def bootstrap_exists():
    return BOOTSTRAP_PATH.exists()


def create_bootstrap_dataset():

    print("=== Bootstrap loomise töövoo algus. ===")

    if not bootstrap_exists():

        print("Bootstrap dataset puudub. Loon uue bootstrapi.")

        download_snapshot()

        snapshot_metadata = load_metadata()

        product_count = filter_estonia_products()

        register_bootstrap_snapshot(
            source_snapshot_date=datetime.fromisoformat(
                snapshot_metadata["downloaded_at"]
            ).date(),
            bootstrap_file=str(BOOTSTRAP_PATH),
            product_count=product_count,
        )

        print("\n=== Bootstrap loomise töövoo lõpp. ===")

        return

    bootstrap_metadata = get_latest_bootstrap_snapshot()

    if bootstrap_metadata is None:

        print("Bootstrap metadata puudub andmebaasis.")

    else:

        snapshot_date = bootstrap_metadata["source_snapshot_date"]

        snapshot_age = (datetime.now(UTC).date() - snapshot_date).days

        print("\nOlemasolev bootstrap:")

        print(f"  Fail: " f"{bootstrap_metadata['bootstrap_file']}")

        print(f"  Source snapshot: " f"{snapshot_date}")

        print(f"  Snapshoti vanus: " f"{snapshot_age} päeva")

        print(f"  Toodete arv: " f"{bootstrap_metadata['product_count']:,}")

        if snapshot_age > BOOTSTRAP_MAX_AGE_DAYS:

            print(
                "\nHOIATUS: bootstrap põhineb "
                f"{snapshot_age} päeva vanusel snapshotil."
            )

        print(
            "\nDelta pipeline korrektseks tööks "
            f"peaks snapshot olema alla "
            f"{BOOTSTRAP_MAX_AGE_DAYS} päeva vana."
        )

    answer = input("\nKas soovid luua uue bootstrapi? [y/N]: ")

    if answer.lower() != "y":

        print("Bootstrap säilitatakse.")
        return

    snapshot_metadata = load_metadata()

    snapshot_date = datetime.fromisoformat(snapshot_metadata["downloaded_at"]).date()

    snapshot_age = (datetime.now(UTC).date() - snapshot_date).days

    print(f"\nViimane allalaaditud snapshot: " f"{snapshot_date}")

    print(f"Snapshoti vanus: " f"{snapshot_age} päeva")

    print(
        "\nDelta pipeline korrektseks tööks "
        f"peaks snapshot olema alla "
        f"{BOOTSTRAP_MAX_AGE_DAYS} päeva vana."
    )

    answer = input("\nKas laadida uus OFF snapshot? [y/N]: ")

    if answer.lower() == "y":

        download_snapshot()

        snapshot_metadata = load_metadata()

    product_count = filter_estonia_products()

    register_bootstrap_snapshot(
        source_snapshot_date=datetime.fromisoformat(
            snapshot_metadata["downloaded_at"]
        ).date(),
        bootstrap_file=str(BOOTSTRAP_PATH),
        product_count=product_count,
    )

    print("\n=== Bootstrap loomise töövoo lõpp. ===")


if __name__ == "__main__":
    create_bootstrap_dataset()
