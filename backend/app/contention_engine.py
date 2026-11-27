import multiprocessing
import time
import os
import tempfile


# ==============================
# CPU CONTENTION
# ==============================

def cpu_worker(stop_event):
    """
    Continuously performs CPU-intensive calculations
    until the stop event is triggered.
    """

    while not stop_event.is_set():

        x = 0

        for i in range(100000):
            x += i * i


# ==============================
# DISK CONTENTION
# ==============================

def disk_worker(stop_event, disk_file):

    """
    Continuously performs disk read/write operations
    until the stop event is triggered.
    """

    block_size = 1024 * 1024  # 1 MB
    data = os.urandom(block_size)

    with open(disk_file, "w+b") as file:

        while not stop_event.is_set():

            file.seek(0)

            file.write(data)
            file.flush()

            file.seek(0)

            file.read(block_size)


# ==============================
# START CPU CONTENTION
# ==============================

def start_cpu_contention(worker_count=None):

    if worker_count is None:

        cpu_count = multiprocessing.cpu_count()

        worker_count = max(1, cpu_count // 2)

    stop_event = multiprocessing.Event()

    workers = []

    for _ in range(worker_count):

        process = multiprocessing.Process(
            target=cpu_worker,
            args=(stop_event,)
        )

        process.start()

        workers.append(process)

    return stop_event, workers


# ==============================
# START DISK CONTENTION
# ==============================

def start_disk_contention():

    stop_event = multiprocessing.Event()

    workers = []

    disk_file = os.path.join(
        tempfile.gettempdir(),
        "disk_contention_test.dat"
    )

    process = multiprocessing.Process(
        target=disk_worker,
        args=(stop_event, disk_file)
    )

    process.start()

    workers.append(process)

    return stop_event, workers


# ==============================
# START COMBINED CONTENTION
# ==============================

def start_combined_contention(worker_count=None):

    """
    Starts CPU and disk contention simultaneously.
    """

    cpu_stop_event, cpu_workers = start_cpu_contention(
        worker_count
    )

    disk_stop_event, disk_workers = start_disk_contention()

    return (
        cpu_stop_event,
        cpu_workers,
        disk_stop_event,
        disk_workers
    )


# ==============================
# STOP CPU CONTENTION
# ==============================

def stop_cpu_contention(stop_event, workers):

    if stop_event is None:
        print("CPU contention was not active.")
        return

    stop_event.set()

    for process in workers:
        process.join(timeout=5)

    for process in workers:
        if process.is_alive():
            process.terminate()
            process.join()

    print("CPU contention stopped.")


# ==============================
# STOP DISK CONTENTION
# ==============================

def stop_disk_contention(stop_event, workers):

    if stop_event is None:
        print("Disk contention was not active.")
        return

    stop_event.set()

    for process in workers:
        process.join(timeout=5)

    for process in workers:
        if process.is_alive():
            process.terminate()
            process.join()

    print("Disk contention stopped.")


# ==============================
# STOP COMBINED CONTENTION
# ==============================

def stop_combined_contention(
    cpu_stop_event,
    cpu_workers,
    disk_stop_event,
    disk_workers
):

    stop_cpu_contention(
        cpu_stop_event,
        cpu_workers
    )

    stop_disk_contention(
        disk_stop_event,
        disk_workers
    )

    print("Combined contention stopped.")