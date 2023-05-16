from pathlib import Path
import argparse
import sys
import os
import socket
import subprocess
from time import sleep
import logging
from datetime import datetime
from utils import *

"""
* Run from Windows Python not supported/tested
* WSL block/unblock working with WUDO

## Levels
Block Level:
0: Nothing blocked
1: Twitter & Linked In
2: Everything but Email
3: Also Email

"""
MUTE = False
powershell="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
cmd="/mnt/c/Windows/System32/cmd.exe"

logger = logging.getLogger("root")
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


try:
    from tqdm import tqdm
except:
    def tqdm(x):
        total = len(x)
        for i,m in enumerate(x):
            sys.stdout.write("Waiting progress: %d%%   \r" % (i/total*100) )
            sys.stdout.flush()
            yield m

root = Path(os.path.dirname(os.path.realpath(__file__)))
_root = root.as_posix()
os.chdir(_root)

def read(path):
    with Path(path).open() as f:
        content = f.read()
    return content

linux_prefix = read("./websites/linux_default").format(socket.gethostname())
windows_prefix = read("./websites/windows_default").format(socket.gethostname())

def get_sites(website_file):
    with (root / website_file).open("r") as f:
        return f.read()

WSL_HOSTS=["G1G2Q13", "PW01AYJG"]

def set_globals(linux=True):
    """ Run from Windows Python not supported/tested """
    global LINUX, HOSTS_FILE_PATH, block_sites, prefix

    if socket.gethostname() in WSL_HOSTS:
        linux=False
    LINUX = True if linux else False

    if linux:
        HOSTS_FILE_PATH="/etc/hosts"
        block_sites=block_sites_linux
        prefix=read("./websites/linux_default").format(socket.gethostname())
        logger.info("ON LINUX")

    else:
        WSL=True
        if WSL:
            HOSTS_FILE_PATH=r"/mnt/c/Windows/System32/drivers/etc/hosts"
            logger.info("ON WSL")
        else:
            HOSTS_FILE_PATH=r"C:\Windows\System32\drivers\etc\hosts"
        block_sites=block_sites_windows
        prefix=read("./websites/windows_default").format(socket.gethostname())
        logger.info(HOSTS_FILE_PATH)

def speak(phrase, delay=0):
    logger.info(phrase)

    if MUTE:
        logger.info("MUTED, not speaking")
        return
    if LINUX:
        os.system('spd-say "{}"'.format(phrase))
    else:
        if not on_zoom_call():
            speak_windows(phrase, delay=delay)

def on_zoom_call():
    if LINUX:
        if "zoom" in os.popen("ps -A").read():
            logger.info("zoom call detected, not speaking")
            return True
    else:
        task_list = run_windows("""cmd.exe /c tasklist /v /fi "imagename eq zoom.exe" """, blocking=True)
        #if "zoom meeting" in task_list.lower():
        if "zoom" in task_list.lower():
            logger.info("zoom call detected, not speaking")
            return True
    return False

def run_windows(command, blocking=True):
    """ Run a system command on Linux using subprocess.Popen
        os.system randomly fails with the powershell tts commands and leaves program hanging
    """
    command += " 2> nul"
    logger.debug(command)
    if blocking:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True) #.wait()
        output, error = process.communicate()
        return output.decode()
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        return process



def speak_windows(phrase, delay=0):
    #command = f"""{powershell} -Command Add-Type -AssemblyName System.Speech; (New-Object -TypeName System.Speech.Synthesis.SpeechSynthesizer).Speak('{phrase}')" """
    #command = f"""{cmd} /c "powershell.exe -Command Add-Type -AssemblyName System.Speech; (New-Object -TypeName System.Speech.Synthesis.SpeechSynthesizer).Speak('{phrase}')" """
    if delay:
        command = f"""powershell.exe -Command "Start-Sleep -Milliseconds {delay*1000}; Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{phrase}');" """
    else:
        command = f"""powershell.exe -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{phrase}');" """

    logger.debug(command)
    run_windows(command, blocking=False)

def flush():
    if LINUX:
        flush_linux()
    else:
        flush_windows()
def flush_linux():
    logger.info("flushing dns...")
    os.system("sudo service network-manager restart")

def flush_windows():
    #type blocked_hosts > hosts
    command = 'cmd.exe /c "cd C:\\Users\\tarchibald && ipconfig /flushdns "'
    #subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    run_windows(command, blocking=False)

def minutes_fmt(time):
    if time == 1:
        return "minute"
    else:
        return "minutes"

def block_sites_linux(level=2):
    logger.info("blocking sites...")
    websites = get_sites_by_level(level, block=True)
    #logger.info(websites)
    logger.info(f"blocking {HOSTS_FILE_PATH}")
    with Path(HOSTS_FILE_PATH).open("w") as f:
        f.write("\n" + prefix)

        for w in websites:
            if w[0] != "#":
                f.write("127.0.0.1 {} \n".format(w))
                f.write("127.0.0.1 www.{} \n".format(w))

def block_sites_windows(level=2):
    logger.info("blocking sites...")
    websites = get_sites_by_level(level, block=True)

    logger.info(f"blocking {HOSTS_FILE_PATH}")
    # temp_path="./hosts.tmp"

    temp_path = HOSTS_FILE_PATH
    with Path(temp_path).open("w") as f:
        f.write("\n" + prefix)
        for w in websites:
            if w[0] != "#":
                f.write("127.0.0.1 {} \n".format(w))
                f.write("127.0.0.1 www.{} \n".format(w))

    # NOT NEEDED or NOT? WORKING
    if temp_path != HOSTS_FILE_PATH:
        command=rf"""/mnt/c/Windows/System32/cmd.exe \c type {temp_path} > "{HOSTS_FILE_PATH}" """
        subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)


    flush_windows()


def whatamidoing(level, block):
    blocking = ["Nothing", "Twitter/LinkedIn", "News/Shopping", "Email"]
    logger.info(f"Target Level: {level}")

    if block:
        logger.info(f"You are blocking {' + '.join(blocking[:level+1])}")
    else:
        logger.info(f"You are UNblocking {' + '.join(blocking[level:])}")


def get_sites_by_level(level=2, block=True):
    """ block (bool): True: include lower levels (0,1,2...); if block=level2, also block level1
                      False: include higher levels (4,3,...); if unblock level2, also unblock level3
    """
    whatamidoing(level,block)
    websites = []
    for source in Path("./websites/").rglob("level*"):
        src_level = source.stem[-1]
        if src_level.isnumeric():
            src_level = int(src_level)
            # Unblock: only return sites at a lower block level than the current one
            if (src_level < level and not block) or (src_level <= level and block):
                logger.info(f"Adding {source}")
                websites += get_sites(source).split()
    return websites

def unblock_sites(level=2):
    """ Recreate hosts block file from scratch
    """
    logger.info("unblocking sites...")
    websites = get_sites_by_level(level, block=False)

    with Path( HOSTS_FILE_PATH).open("w") as f:
        f.write(prefix)
        for w in websites:
            if w[0].strip() != "#":
                f.write("127.0.0.1 {} \n".format(w))
                f.write("127.0.0.1 www.{} \n".format(w))

    flush()

def unblock_all():
    logger.info("unblocking ALL sites...")
    with Path( HOSTS_FILE_PATH).open("w") as f:
        f.write(prefix)
    logger.info(prefix)

def install_block_to_cron(user=""):
    process = subprocess.Popen(f"sudo -s bash {_root}/INSTALL.sh {user}", stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    logger.info("block_hosts installed to crontab")
    #logger.info("RESULT OF INSTALL")
    #logger.info(output.decode())

def get_crontab_text():
    cron_text = "sudo crontab -l"
    process = subprocess.Popen(cron_text, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode()

def install_new_crontab(new_cron_text):
    with (root / "_my_cron").open("w") as f:
        f.write(new_cron_text)
    #process = subprocess.Popen(f"'{new_cron_text}' > {_root}/_my_cron", stdout=subprocess.PIPE, shell=True)
    process = subprocess.call(f"sudo crontab {_root}/_my_cron", stdout=subprocess.PIPE, shell=True)
    os.remove(f"{_root}/_my_cron")

def remove_from_cron():
    remove_from_cron = "sudo crontab -l | sed '/PERSISTENT/p;/block_hosts\/block\.py /d'"
    process = subprocess.Popen(remove_from_cron, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    new_cron_text = output.decode()    
    install_new_crontab(new_cron_text)
    logger.info("block_hosts removed from crontab")

# 59 23 * * * python3 /home/taylor/bashrc/ext/block_hosts/block.py --on > /home/taylor/bashrc/ext/block_hosts/BLOCK.log 2>&1 # PERSISTENT

def sleeper(minutes):
    pause_time = time_debt = 0
    factor = 20
    for i in tqdm(range(minutes*factor)):
        try:
            sleep(int(60/factor))
        except:
            now = datetime.now()
            try:
                input("TIMER IS PAUSED, push any key to continue")
                resume = datetime.now()
                diff = resume - now
                pause_time += diff.seconds
            except:
                response = input("Skip to next? Y/n")
                if response.lower() == "y":
                    return 0
    if pause_time:
        logger.info(f"Timer paused for {pause_time} seconds")
        speak("Timer was paused; should this be deducted from the next cycle?")
        response = input(f"Should I deduct {pause_time} seconds from next cycle? (y/n) (default: yes) ")
        if response.lower() != "n":
            time_debt = int(pause_time/60)
    return time_debt

def unblock_one(item="youtube"):
    # FILTER/DELETE LINES WITH "ITEM" IN THEM
    command = f"sudo -s sed -i '/{item}/d' /etc/hosts" # -i does it inplace
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

def unblock_timer(duration=5, level=2, confirm_break=False):
    break_message = f"Push any key to start {duration} {minutes_fmt(duration)} break"
    try: # Allow user to end break early
        #speak(break_message)
        unblock_sites(level)
        if not confirm_break:
            logger.info(f"Starting {duration} {minutes_fmt(duration)} break")
            speak("Starting clock now")
        else:
            speak(break_message)
            input(break_message)
        sleeper(duration)
    except Exception as e:
        logger.error(e)


num2words = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', \
             6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten', \
            11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen', \
            15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen', \
            19: 'Nineteen', 20: 'Twenty', 30: 'Thirty', 40: 'Forty', \
            50: 'Fifty', 60: 'Sixty', 70: 'Seventy', 80: 'Eighty', \
            90: 'Ninety', 0: 'Zero'}

def n2w(n):
    try:
        return num2words[n]
    except KeyError:
        try:
            return num2words[n-n%10] + num2words[n%10].lower()
        except KeyError:
            return 5


def parser():
    global MUTE
    def parse_int_list(s):
        return [int(x.strip()) for x in s.split(',')]

    parser = argparse.ArgumentParser()
    parser.add_argument('level', nargs='?', default=2)
    parser.add_argument('--unblock', action="store_true")
    parser.add_argument('--unblock_all', action="store_true")
    parser.add_argument('--block', action="store_true")
    parser.add_argument('--off', action="store_true")
    parser.add_argument('--on', action="store_true")
    parser.add_argument('--break_mode', nargs='?', type=parse_int_list, const=[25,5], default=None)
    parser.add_argument('--break_level', default=1, type=int, help="Blocking level during break")
    parser.add_argument('--lunch', nargs='?', const=30, type=int)
    parser.add_argument('--user', default="taylor")
    parser.add_argument('--youtube', nargs='?', const="youtube", type=str)
    parser.add_argument('--site', default=None)
    parser.add_argument('--confirm_break', action="store_true")
    parser.add_argument('--mute', action="store_true")

    opts = parser.parse_args()
    opts.level = int(opts.level)

    MUTE = opts.mute

    epoch = read_completed_cycles()

    if opts.unblock_all:
        unblock_all()
    elif opts.unblock:
        unblock_sites(opts.level)
    elif opts.break_mode is not None:
        #unblock_timer(level=opts.level)
        work_minutes=opts.break_mode[0] if opts.break_mode else 25
        break_minutes=opts.break_mode[1] if len(opts.break_mode)>1 else 5
        work_message="Deep work for {} {}. Ready?".format(work_minutes, minutes_fmt(work_minutes))
        break_message="Break for {} {}. Ready?".format(break_minutes, minutes_fmt(break_minutes))
        while True:
                epoch += 1
                print(f"Starting Epoch: {epoch}/15")
                speak(work_message)
                block_sites(opts.level)
                if True:
                    #speak("Ready?", delay=1.5)
                    input("Ready?")
                speak("GO!!")
                time_debt = sleeper(work_minutes)
                speak(break_message)
                adj_break_minutes = max(break_minutes-time_debt, 0)
                unblock_timer(adj_break_minutes, level=opts.break_level, confirm_break=opts.confirm_break)
                write_completed_cycles(epoch)

    elif opts.lunch is not None:
        unblock_timer(30)
        block_sites(opts.level)
        speak("Blocking websites")

    elif opts.off:
        unblock_sites(opts.level)
        remove_from_cron()
    elif opts.on:
        block_sites(opts.level)
        install_block_to_cron(opts.user)
    elif opts.block:
        block_sites(opts.level)
    elif opts.site:
        unblock_one(opts.site)
    elif opts.youtube is not None:
        unblock_one(opts.youtube)
    elif opts.unblock:
        unblock_sites(opts.level)
    else:
        block_sites(opts.level)

set_globals()

if __name__ == '__main__':
    parser()
