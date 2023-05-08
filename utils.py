import time
from datetime import datetime
from pathlib import  Path
FILE_PARENT = Path(__file__).parent
ROOT = FILE_PARENT / "logs"



def get_today_log_filename():
    filename = datetime.now().strftime('%Y-%m-%d') + '.log'
    return ROOT / filename

def read_completed_cycles():
    try:
        with open(get_today_log_filename(), 'r') as log_file:
            completed_cycles = int(log_file.read().strip())
    except (FileNotFoundError, ValueError):
        completed_cycles = 0

    return completed_cycles


def write_completed_cycles(completed_cycles):
    with open(get_today_log_filename(), 'w') as log_file:
        log_file.write(str(completed_cycles))
