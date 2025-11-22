from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from tqdm import tqdm
import argparse
import logging
import os
import socket
import subprocess
from datetime import datetime
from time import sleep
import requests
import tkinter as tk
from tkinter import messagebox
from block_hosts.utils.idle_timeout import IdleTimeoutHandler
from block_hosts.utils.utils2 import *
from block_hosts.utils.utils import *

ROOT = Path(__file__).resolve().parent

logger = logging.getLogger("root")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
IDLE_TIMEOUT = 300

class SiteBlocker:
    def __init__(self, opts):
        self.opts = opts
        self.WSL = self.is_wsl()
        self.powershell = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
        self.cmd = "/mnt/c/Windows/System32/cmd.exe"
        self.ROOT = Path(__file__).resolve().parent
        self.website_level_definitions = self.ROOT / "websites"
        self.IDLE_TIMEOUT = 300
        self.WSL_HOSTS = ["G1G2Q13", "PW01AYJG"]
        self.linux, self.hosts_path, self.prefix = self.set_globals()
        self.MUTE = False
        self.use_message_boxes = self.opts.use_message_boxes
        self.I = IdleTimeoutHandler()
        self.epoch = read_completed_cycles()

    @staticmethod
    def is_wsl():
        return "microsoft" in os.uname().release

    def set_globals(self):
        if socket.gethostname() in self.WSL_HOSTS:
            on_linux = False
        else:
            on_linux = not self.WSL

        if on_linux:
            hosts_path = "/etc/hosts"
            prefix = self.read(ROOT / "./websites/linux_default").format(socket.gethostname())
        else:
            if self.WSL:
                hosts_path = r"/mnt/c/Windows/System32/drivers/etc/hosts"
            else:
                hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            prefix = self.read(ROOT / "./websites/windows_default").format(socket.gethostname())

        logger.info(hosts_path)
        return on_linux, hosts_path, prefix

    @staticmethod
    def read(path):
        with Path(path).open() as f:
            content = f.read()
        return content

    def create_host_str(self, level):
        logger.info("blocking sites...")
        websites = self.get_sites_by_level(level, include_level=True)
        logger.info(f"prepping {self.hosts_path}")

        # Create long string
        formatted_list = [self.prefix]
        for w in websites:
            if w[0] != "#":
                formatted_list.extend([f"127.0.0.1 {w}",
                                       f"127.0.0.1 www.{w}"
                                       ]
                                      )
        formatted_str = "\n".join(formatted_list)
        return formatted_str

    def set_blocking_level(self, *args, **kwargs):
        return self.block_sites(*args, **kwargs)

    def block_sites(self, level):
        proposed_host_file_str = self.create_host_str(level)
        self.write_to_hosts(proposed_host_file_str, self.hosts_path)
        self.flush()

    def write_to_hosts(self, content, path):
        if self.linux:
            write_to_hosts_linux(content, path)
        else:
            write_to_hosts_windows(content, path)

    def unblock_all(self):
        logger.info("unblocking ALL sites...")
        self.write_to_hosts(self.prefix, self.hosts_path)

    def show_dialog(self, message):
        if self.WSL or not self.linux:
            show_dialog_windows(message)
        else:
            show_dialog_tk(message)

    def flush(self):
        if self.linux:
            flush_linux()
        else:
            flush_windows()

    def get_sites_by_level(self, level=2, include_level=True):
        """ include_level (bool): True: include lower levels (0,1,2...); if block=level2, also block level1
                          False: include higher levels (4,3,...); if unblock level2, also unblock level3
        """
        whatamidoing(level, include_level)
        websites = []
        for source in Path(self.website_level_definitions).rglob("level*"):
            src_level = source.stem[-1]
            if src_level.isnumeric():
                src_level = int(src_level)
                # Unblock: only return sites at a lower block level than the current one
                if (src_level < level and not include_level) or (src_level <= level and include_level):
                    logger.info(f"Adding {source}")
                    websites += get_sites(source).split()
        return websites

    def sleeper(self, minutes):
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
                    response = self.I.prompt("Skip to next? Y/n ", commands=None)
                    print("RESPONSE")
                    print(response)
                    print("END")
                    if response.lower().strip()[-1] == "y":
                        return 0
        if pause_time:
            logger.info(f"Timer paused for {pause_time} seconds")
            self.speak("Timer was paused; should this be deducted from the next cycle?", blocking=False)
            response = self.I.prompt(f"Should I deduct {pause_time} seconds from next cycle? (y/n) (default: yes) ", commands=None)
            if response.lower() != "n":
                time_debt = int(pause_time/60)
        return time_debt

    def unblock_timer(self, duration=5, level=2, confirm_break=False):
        break_message = f"{duration} minute break."
        time_debt = 0
        try: # Allow user to end break early
            if not confirm_break:
                self.speak(break_message + " Starting now!", blocking=True)
            else:
                speak_break = lambda :self.speak(break_message + " Push any key.", blocking=False)
                speak_break()
                if self.use_message_boxes:
                    self.show_dialog(break_message)
                else:
                    self.I.prompt(break_message, commands=[speak_break])

            self.set_blocking_level(level)

            time_debt = self.sleeper(duration)
        except Exception as e:
            logger.error(e)
        return time_debt

    def handle_lunch_break(self):
        self.unblock_timer(30)
        self.block_sites(self.opts.level)
        self.speak("Blocking websites")
    
    def speak(self, message, blocking=False):
        if self.linux:
            self.speak_linux(message, blocking=blocking)
        else:
            self.speak_windows(message, blocking=blocking)      

    def speak_linux(self, phrase, delay=0, blocking=False):
        logger.info(phrase)
        if self.MUTE:
            logger.info("MUTED, not speaking")
            return
        logger.info(f"SAYING {phrase}")
        speak_linux(phrase, delay=delay, blocking=blocking)
        logger.info("DONE")

    def mute(self):
        return on_zoom_call_windows() or (not self.linux and on_work_network() and not bluetooth_sound())

    def speak_windows(self, phrase, delay=0, blocking=False):
        logger.info(phrase)

        if self.MUTE:
            logger.info("MUTED, not speaking")
            return

        if on_zoom_call_windows():
            pass
        elif on_work_network():
            if "go" not in phrase.lower():
                self.system_beep(blocking=blocking)
        else:
            speak_windows(phrase, delay=delay, blocking=blocking)

    def handle_break_mode(self):
        # unblock_timer(level=opts.level)
        work_minutes = adj_work_minutes = self.opts.break_mode[0] if self.opts.break_mode else 25
        break_minutes = self.opts.break_mode[1] if len(self.opts.break_mode) > 1 else 5
        work_message = "Work for {} {}.".format(work_minutes, minutes_fmt(work_minutes))
        break_message = "Break for {} {}."
        ready = "Push any key."  # "Ready?"
        work_message += f" {ready}" if self.opts.confirm_work else " GO! "
        # break_message += " Ready?" if self.opts.confirm_break else " GO! "

        while True:
            self.epoch += 1
            print(f"Starting self.epoch: {self.epoch}/15")
            speak_work = lambda: self.speak(work_message, blocking=False)
            speak_work()
            if self.opts.confirm_work:
                if self.use_message_boxes:
                    self.show_dialog(work_message)
                else:
                    self.I.prompt(f"{ready}", commands=[speak_work])
                self.speak("GO!!")

            self.block_sites(self.opts.level)

            time_debt = self.sleeper(adj_work_minutes)

            adj_break_minutes = max(break_minutes - time_debt, 0)
            write_completed_cycles(self.epoch)
            time_debt = self.unblock_timer(adj_break_minutes,
                                           level=self.opts.break_level,
                                           confirm_break=self.opts.confirm_break)
            adj_work_minutes = max(work_minutes - time_debt, 0)

    def execute(self):
        """ block --youtube will block everything and unblock youtube
            unblock --youtube will ONLY unblock youtube
        """
        done = False
        if self.opts.unblock_all:
            self.unblock_all()
        elif self.opts.unblock and not self.opts.youtube and not self.opts.site:
            self.set_blocking_level(0)
        elif self.opts.break_mode is not None:
            self.handle_break_mode()
        elif self.opts.lunch is not None:
            self.handle_lunch_break()
        elif self.opts.off:
            self.set_blocking_level(self.opts.level)
        elif self.opts.on:
            self.block_sites(self.opts.level)
        elif self.opts.block:
            self.block_sites(self.opts.level)
        else:
            self.block_sites(self.opts.level)

        if self.opts.site:
            remove_sites_entries_in_hosts_file(self.hosts_path, self.opts.site, self.linux)
        if self.opts.youtube:
            unblock_youtube_in_hosts_file(self.hosts_path, self.linux)



def unblock_youtube_in_hosts_file(hosts_file: Path, is_linux: bool = False) -> None:
    """
    Unblocks YouTube by removing any line with a partial match for "youtube"
    from the managed section only.
    """
    from block_hosts.utils.hosts_file_manager import remove_keywords_from_managed_section
    from block_hosts.utils.utils2 import sudo_write_to_hosts_script
    
    use_sudo = is_linux
    sudo_script = sudo_write_to_hosts_script if use_sudo else None
    remove_keywords_from_managed_section(["youtube"], Path(hosts_file), use_sudo=use_sudo, sudo_script_path=sudo_script)

def remove_sites_entries_in_hosts_file(hosts_file: Path, site_keywords: list, is_linux: bool = False) -> None:
    """
    For each domain provided in site_keywords, remove any hosts file entry
    that contains a partial match from the managed section only.
    """
    from block_hosts.utils.hosts_file_manager import remove_keywords_from_managed_section
    from block_hosts.utils.utils2 import sudo_write_to_hosts_script
    
    use_sudo = is_linux
    sudo_script = sudo_write_to_hosts_script if use_sudo else None
    remove_keywords_from_managed_section(site_keywords, Path(hosts_file), use_sudo=use_sudo, sudo_script_path=sudo_script)

def parser(args=None):
    global MUTE
    def parse_int_list(s):
        return [int(x.strip()) for x in s.split(',')]

    def manual_preprocess(args):
        # Assume if the first argument does not start with '-', it's meant to be 'level'
        if args and not args[0].startswith('-'):
            # Prepend '--level' to transform it into a keyword argument
            args = ['--level'] + args
        return args

    parser = argparse.ArgumentParser(
        description="A website blocking utility that modifies the system hosts file to block distracting websites based on configurable block levels and break cycles. Use the various options to block/unblock sites or to start a work/break cycle."
    )
    parser.add_argument('--level', type=int, dest='level', default=3,
                        help='Set the blocking intensity level. Websites from levels up to this value will be blocked. Higher levels block more distracting sites. (default: 3)')
    parser.add_argument('--unblock', action="store_true",
                        help='Disable website blocking by setting the block level to 0.')
    parser.add_argument('--unblock_all', action="store_true",
                        help='Remove all website blocking rules and revert the hosts file to its initial state.')
    parser.add_argument('--block', action="store_true",
                        help='Force blocking of websites using the specified block level.')
    parser.add_argument('--off', action="store_true",
                        help='Apply a blocking configuration based on the provided level (alias for setting blocking level).')
    parser.add_argument('--on', action="store_true",
                        help='Enable website blocking according to the specified level.')
    parser.add_argument('--break_mode', nargs='?', type=parse_int_list, const=[25, 5], default=None,
                        help='Enter work/break mode with a cycle time. Provide two comma-separated values (work_minutes, break_minutes), e.g., "25,5" (default: 25,5).')
    parser.add_argument('--break_level', default=1, type=int,
                        help='Specify the blocking level to use during break intervals (default: 1; typically less restrictive).')
    parser.add_argument('--lunch', nargs='?', const=30, type=int,
                        help='Temporarily disable blocking for a lunch break of specified duration in minutes (default: 30).')
    parser.add_argument('--user', default="taylor",
                        help='Specify the username for the session (default: "taylor").')
    parser.add_argument('--youtube', action='store_true',
                        help='Flag to unblock YouTube by removing related entries from the hosts file')
    parser.add_argument('--site', nargs='+',
                        help='List of domains to remove any partial match from the hosts file')
    parser.add_argument('--skip_confirm_break', action="store_true",
                        help='Skip confirmation prompt before initiating break intervals in break mode.')
    parser.add_argument('--mute', action="store_true",
                        help='Mute speech notifications (disable voice feedback).')
    parser.add_argument('--skip_confirm_work', action="store_true",
                        help='Skip confirmation prompt before starting work intervals in break mode.')
    parser.add_argument('--dont_use_message_boxes', action="store_true",
                        help='Disable graphical message boxes for prompts; use command-line prompts instead.')
                        
    if isinstance(args, str):
        import shlex
        args = shlex.split(args)
    else:
        args = sys.argv[1:]
    args = manual_preprocess(args)
    print(f'RAW ARGS {args}')
    opts = parser.parse_args(args)
    opts.confirm_break = not opts.skip_confirm_break
    opts.confirm_work = not opts.skip_confirm_work
    opts.use_message_boxes = not opts.dont_use_message_boxes
    MUTE = opts.mute

    return opts

def main(args=None):
    opts = parser(args)
    opts.confirm_break = True
    blocker = SiteBlocker(opts)
    print(opts)
    blocker.execute()


if __name__ == "__main__":
    if False:
        args = "3 --break_mode 25,5 --break_level 2"
        #args = "--level 0"
    else:
        args = None
    main(args=args)