from pathlib import Path
import argparse
import sys
import os
import socket

root = Path(os.path.dirname(os.path.realpath(__file__)))

suffix = """
127.0.0.1	localhost
127.0.1.1	{}

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


def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--unblock', action="store_true")
    parser.add_argument('--block', action="store_true") # dummy argument
    opts = parser.parse_args()

    if opts.unblock:
        unblock_sites()
    else:
        block_sites()


if __name__ == '__main__':
    parser()
