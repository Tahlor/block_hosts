
UNBLOCK="0 * * * * python3 /home/$USER/bashrc/ext/block_hosts/block.py --UNBLOCK"
BLOCK="5 * * * * python3 /home/$USER/bashrc/ext/block_hosts/block.py"

crontab_file=$(sudo crontab -l)
echo "$crontab_file" > "/home/$USER/bashrc/ext/block_hosts/backup_cron"
echo "$crontab_file" | grep "${BLOCK:10:100}" # struggles with asterisks

# If grep doesn't find it
if [ $? -ne 0 ]; then

  # Check if crontab exists
  echo $crontab_file | grep -q "no crontab for"
  if [ $? -ne 0 ]; then
    echo "crontab exists"
    sudo crontab -l > mycron
  fi
  #echo new cron into cron file
  echo "$UNBLOCK" >> mycron
  echo "$BLOCK" >> mycron
  #install new cron file
  sudo crontab mycron
  rm mycron
else
  echo "already installed"
fi

#cd /var/spool/cron/crontabs
#grep  'search string' *
