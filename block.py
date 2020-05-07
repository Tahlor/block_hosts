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


def get_sites():
    with (root / "websites.txt").open("r") as f:
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
    with Path("/etc/hosts").open("w") as f:
        f.write(suffix)

def install_block_to_cron():
    process = subprocess.Popen(f"sudo -s bash {_root}/INSTALL.sh", stdout=subprocess.PIPE, shell=True)
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
    remove_from_cron = "sudo crontab -l | sed '/block_hosts\/block\.py/d'"
    process = subprocess.Popen(remove_from_cron, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    new_cron_text = output.decode()    
    install_new_crontab(new_cron_text)
    print("block_hosts removed from crontab")
    
def sleeper(minutes):
    factor = 20
    for i in tqdm(range(10*factor)):
        sleep(int(60/factor))

def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--unblock', action="store_true")
    parser.add_argument('--block', action="store_true")
    parser.add_argument('--off', action="store_true")
    parser.add_argument('--on', action="store_true") 
    parser.add_argument('--ten', action="store_true") 
    opts = parser.parse_args()

    if opts.unblock:
        unblock_sites()
    elif opts.ten:
        print("Unblocking sites in 10 minutes")
        sleeper(10)
        unblock_sites()
        os.system('spd-say "Websites have been unblocked"')
        sleep(5*60)
        block_sites()
    elif opts.off:
        unblock_sites()
        remove_from_cron()
    elif opts.on:
        block_sites()
        install_block_to_cron()
    elif opts.block:
        block_sites()
    else:
        block_sites()


if __name__ == '__main__':
    parser()
