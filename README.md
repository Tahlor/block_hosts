# block_hosts
Block websites using the hosts file on Linux

    block 0 - nothing
    block 1 - block Twitter/linkedin
    block 2 - block news/shopping
    block 3 - block email

    # unblock
    unblock 2 - this is the same as block 1
    we're not really in a block/unblock paradigm anymore, so much as a block-level paradigm

## Set cron job
    sudo crontab -e
    
    0 * * * * python3 /media/data/GitHub/personal_projects/block_hosts/block.py --unblock
    5 * * * * python3 /media/data/GitHub/personal_projects/block_hosts/block.py 


## Run

    sudo python3 /media/data/GitHub/personal_projects/block_hosts/block.py
    sudo python3 /media/data/GitHub/personal_projects/block_hosts/block.py --unblock
    
    

    
## VOLUME
You can either send that HUGE powershell command, or set it up in your "powershell" bashrc.

    @echo off
    # Create profile
    set "ps1_path=%USERPROFILE%\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
    if not exist "%USERPROFILE%\Documents\WindowsPowerShell" mkdir "%USERPROFILE%\Documents\WindowsPowerShell"
    (echo # $PROFILE script) > "%ps1_path%"

    # Add Volume Script to profile
    (echo . `"%USERPROFILE%\bashrc\windows\alias_scripts\profile.ps1`" ) >> "%ps1_path%"

