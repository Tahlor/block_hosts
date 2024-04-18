import warnings
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
from block_hosts.powershell import volume_commands
from block_hosts.volume import get_volume_windows
import requests
import logging
from pathlib import Path
import tempfile

logger = logging

ROOT = Path(__file__).resolve().parent
POWERSHELL_PATH="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
sudo_write_to_hosts_script = ROOT / "sudo_write_to_hosts.sh"


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

def speak_linux(phrase, delay=0, blocking=False):
    if delay:
        sleep(delay)
    if blocking:
        subprocess.Popen(f'/usr/bin/spd-say "{phrase}"', shell=True).wait()
    else:
        subprocess.Popen(f'/usr/bin/spd-say "{phrase}"', shell=True)

def speak_windows(phrase, delay=0, blocking=False, message_volume=.5):
    get_volume = """$CurrentVolume = [Audio]::Volume;"""
    set_volume = """[Audio]::Volume = {};"""
    reset_volume = """[Audio]::Volume = $CurrentVolume;"""
    delay_command = f"Start-Sleep -Milliseconds {delay * 1000};" if delay else ""

    command = f'''
    {get_volume} ;
    {set_volume.format(message_volume)} ;
    {delay_command} ;
    Add-Type –AssemblyName System.Speech;
    (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{phrase}\');
    [Audio]::Volume = $CurrentVolume;
    '''
    logger.debug(command)
    output = run_windows(command, blocking=blocking, executable='powershell.exe')
    logger.debug(output)


# def speak(phrase, delay=0, blocking=False, ):
#     logger.info(phrase)
#
#     if MUTE and not LINUX:
#         logger.info("MUTED, not speaking")
#         show_dialog(phrase)
#         return
#     if LINUX:
#         print(f"SAYING {phrase}")
#         subprocess.Popen(f'/usr/bin/spd-say {phrase}', shell=True)
#         print("DONE")
#     else:
#         if on_zoom_call():
#             pass
#         elif on_work_network():
#             if "go" not in phrase.lower():
#                 system_beep(blocking=blocking)
#         else:
#             speak_windows(phrase, delay=delay, blocking=blocking)
#         if ENABLE_MESSAGE_BOXES:
#             show_dialog(phrase)

def system_beep_windows(blocking=False):
    try:
        logger.debug("BEEP!!")
        # All of these should work
        sound_command = """(New-Object System.Media.SoundPlayer $(Get-ChildItem -Path $env:windir\Media\Alarm03.wav).FullName).PlaySync()"""
        out = run_windows(sound_command, blocking=blocking, executable=POWERSHELL_PATH)
    except Exception as e:
        print(f"An error occurred while beeping: {e}")

def on_work_network():
    try:
        # this just tests VPN, not work network per se
        response = requests.get("myfamily.int", timeout=1)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def bluetooth_sound():
    # check if on bluetooth headphones
    warnings.warn("bluetooth_sound not implemented")
    return False

def on_zoom_call_windows():
    zoom_powershell = """if ($zoomProcess = Get-Process -Name Zoom -EA 0) { (Get-NetUDPEndpoint -OwningProcess $zoomProcess.Id -EA 0 | Measure-Object).Count } else { 0 }"""
    output = run_windows(zoom_powershell, blocking=True, executable=POWERSHELL_PATH)
    logger.debug(f"ZOOM OUTPUT: {output}")
    if output != "0":
        return True
    return False

def on_zoom_call_linux():
    if "zoom" in os.popen("ps -A").read():
        logger.info("zoom call detected, not speaking")
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

    command_no_linebreaks = command.replace("\n"," ")
    #logger.info("""{} -Command "& {{ {} }} " """.format(executable, command_no_linebreaks))
    #logger.info("""{} -Command "& {{ {} }} " """.format(executable, command_no_linebreaks))
    logger.debug(f'{executable} -Command "& {{{{ {command_no_linebreaks} }}}}"')

    if blocking:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable=executable) #.wait()
        output, error = process.communicate()
        return clean_powershell(output.decode())
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable=executable)
        return process

def show_dialog_windows(message):
    powershell_command = f"{POWERSHELL_PATH} -Command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('{message}')\""
    print(powershell_command)
    subprocess.run(powershell_command, shell=True)

def show_dialog_tk(message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Message", message)
    root.destroy()

def flush_linux():
    logger.info("flushing dns...")
    #os.system("sudo service network-manager restart")
    #os.system("sudo systemctl restart NetworkManager.service")
    os.system(f"sudo {str(ROOT)}/sudo_restart_network.sh")

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

def write_to_hosts_linux(formatted_str, path=None):
    command = f"sudo {sudo_write_to_hosts_script} '{formatted_str}' '{path}'"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)


def write_to_hosts_linux(formatted_str: str, path: str = "/etc/hosts"):
    """
    Update the /etc/hosts file with new content.

    Args:
        formatted_str (str): The new content for the /etc/hosts file.
        script_path (str): Path to the bash script for updating /etc/hosts.
        path (str, optional): The path to the /etc/hosts file. Defaults to "/etc/hosts".
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file_path = Path(tmp_file.name)
        tmp_file_path.write_text(formatted_str)
    command = ["sudo", sudo_write_to_hosts_script, str(tmp_file_path), path]
    result = subprocess.run(command, check=True)
    tmp_file_path.unlink()

def write_to_hosts_windows(formatted_str, path=None):
    with Path(path).open("w") as f:
        f.write(formatted_str)

def move_file_windows(src, dest):
    """ May be useful on windows if you can't directly write to a file
    """
    command=rf"""/mnt/c/Windows/System32/cmd.exe \c type {src} > "{dest}" """
    subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)

def input2(text):
    try:
        return input(text) # or raw_input() for Python 2
    except:
        raise KeyboardInterrupt



def unblock_one(item="youtube", hosts_path="/etc/hosts"):
    # FILTER/DELETE LINES WITH "ITEM" IN THEM
    command = f"sudo -s sed -i '/{item}/d' {hosts_path}" # -i does it inplace
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

def whatamidoing(level, block):
    blocking = ["Nothing", "Twitter/LinkedIn", "News/Shopping", "Email"]
    logger.info(f"Target Level: {level}")

    if block:
        logger.info(f"You are blocking {' + '.join(blocking[:level+1])}")
    else:
        logger.info(f"You are UNblocking {' + '.join(blocking[level:])}")


def get_sites(website_file):
    with (website_file).open("r") as f:
        return f.read()
