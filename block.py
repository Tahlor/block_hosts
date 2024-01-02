import tkinter as tk
from tkinter import messagebox

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
from powershell import volume_commands
from volume import get_volume_windows
import requests

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
WSL = is_wsl()
powershell="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
cmd="/mnt/c/Windows/System32/cmd.exe"
IDLE_TIMEOUT = 300
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


I = IdleTimeoutHandler(timeout = IDLE_TIMEOUT, commands=None, run_once=False)

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
    global LINUX, HOSTS_FILE_PATH, block_sites, prefix, WSL

    if socket.gethostname() in WSL_HOSTS:
        linux=False
    LINUX = True if linux else False

    if linux:
        HOSTS_FILE_PATH="/etc/hosts"
        block_sites=block_sites_linux
        prefix=read("./websites/linux_default").format(socket.gethostname())
        logger.info("ON LINUX")

    else:
        if WSL:
            HOSTS_FILE_PATH=r"/mnt/c/Windows/System32/drivers/etc/hosts"
            logger.info("ON WSL")
        else:
            HOSTS_FILE_PATH=r"C:\Windows\System32\drivers\etc\hosts"
        block_sites=block_sites_windows
        prefix=read("./websites/windows_default").format(socket.gethostname())
        logger.info(HOSTS_FILE_PATH)

def speak(phrase, delay=0, blocking=False):
    logger.info(phrase)

    if MUTE:
        logger.info("MUTED, not speaking")
        show_dialog(phrase)
        return
    if LINUX:
        os.system('spd-say "{}"'.format(phrase))
    else:
        if on_zoom_call():
            pass
        elif on_work_network():
            if "go" not in phrase.lower():
                system_beep(blocking=blocking)
        else:
            speak_windows(phrase, delay=delay, blocking=blocking)
        if ENABLE_MESSAGE_BOXES:
            show_dialog(phrase)

def system_beep(blocking=False):
    try:
        logger.debug("BEEP!!")
        # All of these should work
        sound_command = """(New-Object System.Media.SoundPlayer $(Get-ChildItem -Path $env:windir\Media\Alarm03.wav).FullName).PlaySync()"""
        # sound_command = """(New-Object System.Media.SoundPlayer 'C:\\Windows\\Media\\Alarm03.wav').PlaySync()"""
        # sound_command = "[System.Media.SystemSounds]::Question.Play()" # edit going to System Sounds and changing QUESTION
        # sound_command = [System.Console]::Beep()
        out = run_windows(sound_command, blocking=blocking, executable=powershell)
    except Exception as e:
        print(f"An error occurred while beeping: {e}")

def mute_speaker():
    return on_zoom_call() or (not LINUX and on_work_network() and not bluetooth_sound())

def on_work_network():
    # Right now, this just tests if I'm at work OR on the VPN, actually might just be for the VPN
    # maybe try using the work gateway (wifi and hardline)
    try:
        response = requests.get("10.74.9.18", timeout=1)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def bluetooth_sound():
    return False

def on_zoom_call():
    if LINUX:
        if "zoom" in os.popen("ps -A").read():
            logger.info("zoom call detected, not speaking")
            return True
    else:
        #task_list = run_windows("""cmd.exe /c tasklist /v /fi "imagename eq zoom.exe" """, blocking=True)
        #         if "zoom" in task_list.lower():
        #if "zoom meeting" in task_list.lower() or "n/a" in task_list.lower():
        #    logger.info("zoom call detected, not speaking")
        #    return True
        zoom_powershell = """if ($zoomProcess = Get-Process -Name Zoom -EA 0) { (Get-NetUDPEndpoint -OwningProcess $zoomProcess.Id -EA 0 | Measure-Object).Count } else { 0 }"""
        output = run_windows(zoom_powershell, blocking=True, executable=powershell)
        logger.debug(f"ZOOM OUTPUT: {output}")
        if output != "0":
            return True
    return False

def clean_powershell(output):
    if isinstance(output,str):
        return output.replace("Profile loaded successfully\n","").strip()
    else:
        return output

def run_windows(command, blocking=True, executable=None):
    """ Run a system command on Linux using subprocess.Popen
        os.system randomly fails with the powershell tts commands and leaves program hanging
    """
    if executable is None:
        command += " 2> nul"

    logger.debug(command)
    if blocking:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable=executable) #.wait()
        output, error = process.communicate()
        return clean_powershell(output.decode())
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable=executable)
        return process


def show_dialog(message):
    """
    Display a dialog box with the given message.

    Args:
        message (str): The message to display in the dialog box.
    """
    if WSL or not LINUX:
        show_dialog_windows(message)
    else:
        show_dialog_tk(message)


def show_dialog_windows(message):
    powershell_command = f'{powershell} -Command "[System.Windows.MessageBox]::Show(\'{message}\')"'
    powershell_command = f"{powershell} -Command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('{message}')\""
    print(powershell_command)
    subprocess.run(powershell_command, shell=True)

def show_dialog_tk(message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Message", message)
    root.destroy()

def speak_windows(phrase, delay=0, blocking=False, message_volume=.5):
    #command = f"""{powershell} -Command Add-Type -AssemblyName System.Speech; (New-Object -TypeName System.Speech.Synthesis.SpeechSynthesizer).Speak('{phrase}')" """
    #command = f"""{cmd} /c "powershell.exe -Command Add-Type -AssemblyName System.Speech; (New-Object -TypeName System.Speech.Synthesis.SpeechSynthesizer).Speak('{phrase}')" """
    # {volume_commands};
    #current_volume=get_volume_windows()
    
    get_volume = """$CurrentVolume = [Audio]::Volume;"""
    set_volume = """[Audio]::Volume = {};"""
    reset_volume = """[Audio]::Volume = $CurrentVolume;"""
    delay_command = f"Start-Sleep -Milliseconds {delay*1000};" if delay else ""

    command = f'''
    {get_volume} ;
    {set_volume.format(message_volume)} ;
    {delay_command} ;
    Add-Type –AssemblyName System.Speech;
    (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{phrase}\');
    [Audio]::Volume = $CurrentVolume;
    '''
    #f'{set_volume.format(current_volume)} '

    #Start-Sleep -Seconds 5;

    logger.debug(command)
    output = run_windows(command, blocking=blocking, executable='powershell.exe')
    logger.debug(output)

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

def input2(text):
    try:
        return input(text) # or raw_input() for Python 2
    except:
        raise KeyboardInterrupt

def sleeper(minutes):
    pause_time = time_debt = 0
    factor = 20
    for i in tqdm(range(minutes*factor)):
        try:
            sleep(int(60/factor))
        except:
            now = datetime.now()
            try:
                input2("TIMER IS PAUSED, push any key to continue")
                resume = datetime.now()
                diff = resume - now
                pause_time += diff.seconds
            except KeyboardInterrupt:
                response = I.prompt("Skip to next? Y/n ", commands=None)
                print("RESPONSE")
                print(response)
                print("END")
                if response.lower().strip()[-1] == "y":
                    return 0
    if pause_time:
        logger.info(f"Timer paused for {pause_time} seconds")
        speak("Timer was paused; should this be deducted from the next cycle?", blocking=False)
        response = I.prompt(f"Should I deduct {pause_time} seconds from next cycle? (y/n) (default: yes) ", commands=None)
        if response.lower() != "n":
            time_debt = int(pause_time/60)
    return time_debt

def unblock_one(item="youtube"):
    # FILTER/DELETE LINES WITH "ITEM" IN THEM
    command = f"sudo -s sed -i '/{item}/d' /etc/hosts" # -i does it inplace
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

def unblock_timer(duration=5, level=2, confirm_break=False):
    break_message = f"{duration} minute break."
    unblock_sites(level)
    time_debt = 0
    try: # Allow user to end break early
        if not confirm_break:
            speak(break_message + " Starting now!", blocking=True)
        else:
            speak_break = lambda :speak(break_message + " Push any key.", blocking=False)
            speak_break()
            I.prompt(break_message, commands=[speak_break])
        time_debt = sleeper(duration)
    except Exception as e:
        logger.error(e)
    return time_debt

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
    global MUTE, ENABLE_MESSAGE_BOXES
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
    parser.add_argument('--confirm_work', action="store_true")
    parser.add_argument('--no_message_box', action="store_true")

    opts = parser.parse_args()
    opts.level = int(opts.level)

    MUTE = opts.mute
    ENABLE_MESSAGE_BOXES = not opts.no_message_box

    epoch = read_completed_cycles()

    #opts.confirm_work = True
    opts.confirm_break = True

    if opts.unblock_all:
        unblock_all()
    elif opts.unblock:
        unblock_sites(opts.level)

    elif opts.break_mode is not None:
        #unblock_timer(level=opts.level)
        work_minutes=adj_work_minutes=opts.break_mode[0] if opts.break_mode else 25
        break_minutes=opts.break_mode[1] if len(opts.break_mode)>1 else 5
        work_message="Work for {} {}.".format(work_minutes, minutes_fmt(work_minutes))
        break_message="Break for {} {}."
        ready = "Push any key." # "Ready?"
        work_message += f" {ready}" if opts.confirm_work else " GO! "
        #break_message += " Ready?" if opts.confirm_break else " GO! "
        
        while True:
                epoch += 1
                print(f"Starting Epoch: {epoch}/15")
                speak_work = lambda: speak(work_message, blocking=False)
                speak_work()
                if opts.confirm_work:
                    I.prompt(f"{ready}", commands=[speak_work])
                    speak("GO!!")
                block_sites(opts.level)

                time_debt = sleeper(adj_work_minutes)

                adj_break_minutes = max(break_minutes-time_debt, 0)
                write_completed_cycles(epoch)
                time_debt = unblock_timer(adj_break_minutes, level=opts.break_level, confirm_break=opts.confirm_break)
                adj_work_minutes = max(work_minutes-time_debt, 0)

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
