from pathlib import Path
import argparse
import sys
import os
import socket
import subprocess
from time import sleep

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

suffix = """
127.0.0.1    localhost
127.0.1.1    {}

::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters""".format(socket.gethostname())


def get_sites(website_file="websites.txt"):
    with (root / website_file).open("r") as f:
        return f.read()


def block_sites():
    print("blocking sites...")
    websites = get_sites().split()
    with Path("/etc/hosts").open("w") as f:
        for w in websites:
            f.write("127.0.0.1 {} \n".format(w))
            f.write("127.0.0.1 www.{} \n".format(w))

        f.write("\n" + suffix)


def unblock_sites():
    print("unblocking sites...")
    websites = get_sites("always_block_websites.txt").split()
    with Path("/etc/hosts").open("w") as f:
        for w in websites:
            f.write("127.0.0.1 {} \n".format(w))
            f.write("127.0.0.1 www.{} \n".format(w))
        f.write(suffix)

def install_block_to_cron(user=""):
    process = subprocess.Popen(f"sudo -s bash {_root}/INSTALL.sh {user}", stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    print("block_hosts installed to crontab")
    #print("RESULT OF INSTALL")
    #print(output.decode())

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
    print("block_hosts removed from crontab")

# 59 23 * * * python3 /home/taylor/bashrc/ext/block_hosts/block.py --on > /home/taylor/bashrc/ext/block_hosts/BLOCK.log 2>&1 # PERSISTENT  

def sleeper(minutes):
    factor = 20
    for i in tqdm(range(minutes*factor)):
        sleep(int(60/factor))

def unblock_one(item="youtube"):
    # FILTER/DELETE LINES WITH "ITEM" IN THEM
    command = f"sudo -s sed -i '/{item}/d' /etc/hosts" # -i does it inplace
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

def unblock_timer(duration=5):
    break_message = "You got a {} minute break!".format(duration)
    try:
    # Allow user to end break early
        os.system('spd-say "{}"'.format(break_message))
        input(break_message)
        unblock_sites()

        sleeper(duration)
    except:
        pass


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
    parser = argparse.ArgumentParser()
    parser.add_argument('--unblock', action="store_true")
    parser.add_argument('--block', action="store_true")
    parser.add_argument('--off', action="store_true")
    parser.add_argument('--on', action="store_true")
    parser.add_argument('--break_mode', nargs='?', const=60, type=int)
    parser.add_argument('--lunch', nargs='?', const=30, type=int)
    parser.add_argument('--user', default="taylor")
    parser.add_argument('--youtube', nargs='?', const="youtube", type=str)
    parser.add_argument('--site', default=None) 

    opts = parser.parse_args()

    break_message = "You got a {} minute break!"
    if opts.unblock:
        unblock_sites()
    elif opts.break_mode is not None:
        unblock_timer()
        while True:
                block_sites()
                os.system('spd-say "Blocking websites"')
                print("Blocking sites for {} minutes".format(opts.break_mode))
                sleeper(opts.break_mode)
                os.system('spd-say "{}"'.format(break_message))
                unblock_timer()
    elif opts.lunch is not None:
        unblock_timer(30)
        block_sites()
        os.system('spd-say "Blocking websites"')

    elif opts.off:
        unblock_sites()
        remove_from_cron()
    elif opts.on:
        block_sites()
        install_block_to_cron(opts.user)
    elif opts.block:
        block_sites()
    elif opts.site:
        unblock_one(opts.site)
    elif opts.youtube is not None:
        unblock_one(opts.youtube)
    elif opts.unblock:
        unblock_sites()
    else:
        block_sites()


if __name__ == '__main__':
    parser()
