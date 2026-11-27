import subprocess
import os
import time
import hashlib
import shutil
from pathlib import Path
from .contention_engine import (
    start_cpu_contention,
    stop_cpu_contention,
    start_disk_contention,
    stop_disk_contention,
    start_combined_contention,
    stop_combined_contention
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESTIC_PATH = PROJECT_ROOT / "tools" / "restic.exe"

REPOSITORY = PROJECT_ROOT / "experiment_workspace" / "backup_repository"

DATASETS_DIR = PROJECT_ROOT / "experiment_workspace" / "datasets"

RESTORE_DIR = PROJECT_ROOT / "experiment_workspace" / "restored_data"

RESTIC_PASSWORD = "DR_Project_Test_Password_2026"


def run_restic_command(command):

    env = os.environ.copy()
    env["RESTIC_PASSWORD"] = RESTIC_PASSWORD

    result = subprocess.run(
        [str(RESTIC_PATH)] + command,
        env=env,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print("ERROR:")
        print(result.stderr)

        raise RuntimeError(result.stderr)

    return result


def calculate_hashes(directory):

    hashes = {}

    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory}"
        )

    for file_path in directory.rglob("*"):

        if file_path.is_file():

            sha256 = hashlib.sha256()

            with open(file_path, "rb") as file:

                for chunk in iter(
                    lambda: file.read(1024 * 1024),
                    b""
                ):

                    sha256.update(chunk)

            relative_path = str(
                file_path.relative_to(directory)
            )

            hashes[relative_path] = sha256.hexdigest()

    return hashes


def perform_backup(dataset):

    print("\nStarting backup experiment...")

    print(f"Dataset: {dataset}")

    start_time = time.perf_counter()

    result = run_restic_command([
        "backup",
        "--repo",
        str(REPOSITORY),
        str(dataset)
    ])

    end_time = time.perf_counter()

    backup_duration = end_time - start_time

    print(result.stdout)

    print(f"Backup Duration: {backup_duration:.4f} seconds")

    return backup_duration


def find_restored_dataset(dataset_name):

    """
    Automatically locate the restored dataset directory.
    Avoid hardcoding the Windows username or project path.
    """

    matches = list(
        RESTORE_DIR.rglob(dataset_name)
    )

    for match in matches:

        if match.is_dir():

            files = list(match.rglob("*.bin"))

            if files:
                return match

    raise FileNotFoundError(
        f"Could not locate restored dataset: {dataset_name}"
    )


def perform_restore(target_rto_seconds, dataset):

    print("\nStarting restoration experiment...")

    if RESTORE_DIR.exists():

        shutil.rmtree(RESTORE_DIR)

    RESTORE_DIR.mkdir(parents=True, exist_ok=True)

    start_time = time.perf_counter()

    result = run_restic_command([
        "restore",
        "--repo",
        str(REPOSITORY),
        "latest",
        "--target",
        str(RESTORE_DIR)
    ])

    end_time = time.perf_counter()

    restore_duration = end_time - start_time

    print(result.stdout)

    print(f"Restore Duration: {restore_duration:.4f} seconds")

    # Automatically discover the restored dataset
    restored_dataset = find_restored_dataset(
        dataset.name
    )

    print(f"Restored dataset located at: {restored_dataset}")

    # Integrity verification
    print("\nVerifying data integrity...")

    original_hashes = calculate_hashes(dataset)

    restored_hashes = calculate_hashes(restored_dataset)

    integrity_passed = (
        original_hashes == restored_hashes
    )

    integrity_status = (
        "PASS" if integrity_passed else "FAIL"
    )

    rto_passed = (
        restore_duration <= target_rto_seconds
    )

    rto_status = (
        "PASS" if rto_passed else "FAIL"
    )

    print(f"Integrity Verification: {integrity_status}")

    print(f"Target RTO: {target_rto_seconds} seconds")

    print(f"RTO Status: {rto_status}")

    return {
        "restore_duration_seconds": restore_duration,
        "integrity_status": integrity_status,
        "rto_status": rto_status,
        "recovery_success": integrity_passed,
        "rto_achieved": rto_passed
    }
def run_experiment(
    dataset_size_mb=100,
    target_rto_seconds=10,
    scenario="NORMAL"
):
    valid_scenarios = {
        "NORMAL",
        "CPU_CONTENTION",
        "DISK_CONTENTION",
        "COMBINED",
        "COMBINED_CONTENTION"
    }

    if scenario not in valid_scenarios:
        raise ValueError(
            f"Invalid scenario: {scenario}"
        )

    dataset_name = f"dataset_{dataset_size_mb}mb"

    dataset = DATASETS_DIR / dataset_name

    # Generate dataset if it does not exist
    if not dataset.exists():

        from .experiment_engine import generate_dataset

        dataset = generate_dataset(
            size_mb=dataset_size_mb,
            file_count=10
        )

    print("\n===================================")
    print("DISASTER RECOVERY EXPERIMENT")
    print("===================================")

    print(f"Dataset Size: {dataset_size_mb} MB")
    print(f"Target RTO: {target_rto_seconds} seconds")
    print(f"Scenario: {scenario}")

    # Backup is performed without artificial contention
    backup_duration = perform_backup(dataset)

    # Contention variables
    cpu_stop_event = None
    cpu_workers = []

    disk_stop_event = None
    disk_workers = []

    # ==============================
    # START CONTENTION
    # ==============================

    if scenario == "CPU_CONTENTION":

        print("\nStarting CPU contention...")

        cpu_stop_event, cpu_workers = start_cpu_contention()

        print(f"CPU workers started: {len(cpu_workers)}")

    elif scenario == "DISK_CONTENTION":

        print("\nStarting disk contention...")

        disk_stop_event, disk_workers = start_disk_contention()

        print("Disk contention started.")


    elif scenario in ["COMBINED", "COMBINED_CONTENTION"]:

        print("\nStarting combined contention...")

        (
            cpu_stop_event,
            cpu_workers,
            disk_stop_event,
            disk_workers
        ) = start_combined_contention()

        print(f"CPU workers started: {len(cpu_workers)}")
        print(f"Disk workers started: {len(disk_workers)}")

    try:

        # ==============================
        # RESTORATION
        # ==============================

        print("\nStarting restoration experiment...")

        restore_results = perform_restore(
            target_rto_seconds,
            dataset
        )

    finally:

        # ==============================
        # STOP CONTENTION
        # ==============================

        if scenario == "CPU_CONTENTION":

            stop_cpu_contention(
                cpu_stop_event,
                cpu_workers
            )

        elif scenario == "DISK_CONTENTION":

            stop_disk_contention(
                disk_stop_event,
                disk_workers
            )

        elif scenario in ["COMBINED", "COMBINED_CONTENTION"]:
            stop_combined_contention(
                cpu_stop_event,
                cpu_workers,
                disk_stop_event,
                disk_workers
            )

    results = {
        "dataset_size_mb": dataset_size_mb,
        "scenario": scenario,
        "backup_duration_seconds": backup_duration,
        **restore_results
    }

    print("\n========== FINAL RESULTS ==========")

    print(results)

    return results

if __name__ == "__main__":

    results = run_experiment(
        dataset_size_mb=500,
        target_rto_seconds=10
    )