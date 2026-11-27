import os
import hashlib
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

WORKSPACE = PROJECT_ROOT / "experiment_workspace"

DATASETS_DIR = WORKSPACE / "datasets"


def generate_dataset(size_mb=100, file_count=10):

    dataset_dir = DATASETS_DIR / f"dataset_{size_mb}mb"

    dataset_dir.mkdir(parents=True, exist_ok=True)

    file_size = (size_mb * 1024 * 1024) // file_count

    print(f"Generating {size_mb} MB dataset...")

    start_time = time.perf_counter()

    for i in range(file_count):

        file_path = dataset_dir / f"file_{i + 1}.bin"

        with open(file_path, "wb") as file:

            file.write(os.urandom(file_size))

    elapsed = time.perf_counter() - start_time

    print(f"Dataset generated in {elapsed:.2f} seconds")

    return dataset_dir


def calculate_dataset_hashes(directory):

    hashes = {}

    for file_path in Path(directory).rglob("*"):

        if file_path.is_file():

            sha256 = hashlib.sha256()

            with open(file_path, "rb") as file:

                for chunk in iter(
                    lambda: file.read(1024 * 1024),
                    b""
                ):

                    sha256.update(chunk)

            hashes[str(file_path.relative_to(directory))] = (
                sha256.hexdigest()
            )

    return hashes


if __name__ == "__main__":

    dataset = generate_dataset(
        size_mb=100,
        file_count=10
    )

    hashes = calculate_dataset_hashes(dataset)

    print("\nDataset files:")

    for filename, digest in hashes.items():

        print(filename, digest)

    print(f"\nTotal files: {len(hashes)}")