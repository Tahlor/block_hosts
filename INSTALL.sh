#!/bin/bash

DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]:-$0}"; )" &> /dev/null && pwd 2> /dev/null; )";
LOCAL_USER=${1-$(logname)}

# 59 23 * * * python3 /home/taylor/bashrc/ext/block_hosts/block.py --on --user taylor > /home/taylor/bashrc/ext/block_hosts/BLOCK.log 2>&1 # PERSISTENT

UNBLOCK="0 * * * * python3 /home/$LOCAL_USER/bashrc/ext/block_hosts/block_hosts/block.py --unblock >> /home/$LOCAL_USER/bashrc/ext/block_hosts/block_hosts/BLOCK.log 2>&1"
BLOCK="5 * * * * python3 /home/$LOCAL_USER/bashrc/ext/block_hosts/block_hosts/block.py --block >> /home/$LOCAL_USER/bashrc/ext/block_hosts/block_hosts/BLOCK.log 2>&1"
crontab_file=$(sudo crontab -l)
echo "$crontab_file" > "/home/$LOCAL_USER/bashrc/ext/block_hosts/block_hosts/backup_cron"
echo "$crontab_file" | grep -F "${BLOCK:10:100}" # ignore exact timing or if commented out etc.

# If grep doesn't find it
if [ $? -ne 0 ]; then
  # Check if crontab exists
  echo $crontab_file | grep -q "no crontab for"
  if [ $? -ne 0 ]; then
    echo "crontab exists"
    sudo crontab -l > mycron
  fi

  # Check if ends with double newline
  if ! [ -z "$(tail -n 1 mycron)" ]; then
        printf "\n" >> mycron
  fi

  # echo new cron into cron file
  echo "$UNBLOCK" >> mycron
  echo "$BLOCK" >> mycron

  #install new cron file
  sudo crontab mycron
  #rm mycron
else
  echo "already installed"
fi

#cd /var/spool/cron/crontabs
#grep  'search string' *

chmod +x $DIR/utils/sudo_write_to_hosts.sh

# Add sudo_write_to_hosts to visudo if it's not there
if [ ! -f /etc/sudoers.d/sudo_write_to_hosts ]; then
    echo "Creating sudoers file for sudo_write_to_hosts.sh script"
    new_sudoers_file="/etc/sudoers.d/block_hosts"
    touch $new_sudoers_file
    chmod 0440 $new_sudoers_file
    echo "taylor ALL=(root) NOPASSWD: $DIR/utils/sudo_write_to_hosts.sh" | EDITOR="tee -a" visudo -f $new_sudoers_file
    echo "taylor ALL=(root) NOPASSWD: $DIR/utils/sudo_restart_network.sh" | EDITOR="tee -a" visudo -f $new_sudoers_file
fi

