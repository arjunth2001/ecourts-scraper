from datetime import datetime, timedelta
import multiprocessing
import os
# These parameters needs to be changed..
FROM_DATE = '01-05-2019'  # From date of whole range
TO_DATE = '01-05-2021'  # To date of whole range
START_DISTRICT = 0
END_DISTRICT = 75  # (Can be max 75)
PROCESSESS = 12  # Max Number of Processes
LOG_DIR = "./log"  # Directory to write logs in
NUM_CHUNKS = 180  # Number of days in each chunk
# Leave untouched for now
DATE_FORMAT = '%d-%m-%Y'
DATE_STEP = timedelta(days=1)


def _strptime(string):
    return datetime.strptime(string, DATE_FORMAT)


def _strftime(date):
    return date.strftime(DATE_FORMAT)


def _date_range_parameters(start, end, span_days):
    start = _strptime(start)
    end = _strptime(end)
    span = timedelta(days=span_days)
    return start, end, span


def forward_date_range(start, end, span_days):
    start, end, span = _date_range_parameters(start, end, span_days)
    stop = end - span

    while start < stop:
        current = start + span
        yield _strftime(start), _strftime(current)
        start = current + DATE_STEP

    yield _strftime(start), _strftime(end)


def run(chunk):
    from_date, to_date = chunk
    command = f"python ./server_download.py {from_date} {to_date} {START_DISTRICT} {END_DISTRICT} {from_date}_{to_date}.png > {LOG_DIR}/{from_date}_{to_date}.txt"
    print(command)
    os.system(command)


if __name__ == "__main__":
    try:
        os.makedirs(LOG_DIR)
    except:
        pass
    chunks = list(forward_date_range(FROM_DATE, TO_DATE, NUM_CHUNKS))
    with multiprocessing.Pool(processes=PROCESSESS) as pool:
        pool.map(run, chunks)
