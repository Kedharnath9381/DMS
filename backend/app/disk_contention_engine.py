import os
import threading
import time
import tempfile


def disk_worker(stop_event, temp_file, block_size=4 * 1024 * 1024):
    """
    Continuously performs controlled disk read/write operations
    on a temporary file until stop_event is triggered.
    """

    data = os.urandom(block_size)

    with open(temp_file, "wb") as file:
        # Create a fixed-size temporary file (64 MB)
        for _ in range(16):
            file.write(data)

        file.flush()
        os.fsync(file.fileno())

    while not stop_event.is_set():

        # Write workload
        with open(temp_file, "r+b") as file:
            for _ in range(16):
                if stop_event.is_set():
                    break

                file.seek(0)
                file.write(data)
                file.flush()

        # Read workload
        with open(temp_file, "rb") as file:
            while not stop_event.is_set():
                chunk = file.read(block_size)

                if not chunk:
                    break


def start_disk_contention():
    """
    Starts controlled disk I/O contention.
    Creates a temporary 64 MB file.
    """

    stop_event = threading.Event()

    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, "dr_disk_contention_test.tmp")

    worker = threading.Thread(
        target=disk_worker,
        args=(stop_event, temp_file),
        daemon=True
    )

    worker.start()

    # Allow the workload to initialize
    time.sleep(1)

    return stop_event, worker, temp_file


def stop_disk_contention(stop_event, worker, temp_file):
    """
    Stops the workload and removes the temporary file.
    """

    stop_event.set()

    worker.join(timeout=5)

    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except PermissionError:
            print("Warning: Temporary contention file could not be removed.")

    print("Disk contention stopped.")