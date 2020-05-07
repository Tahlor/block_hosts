# block_hosts
Block websites using the hosts file on Linux

## Set cron job
    sudo crontab -e
    
    0 * * * * python3 /media/data/GitHub/personal_projects/block_hosts/block.py --unblock
    5 * * * * python3 /media/data/GitHub/personal_projects/block_hosts/block.py 


## Run

    sudo python3 /media/data/GitHub/personal_projects/block_hosts/block.py
    sudo python3 /media/data/GitHub/personal_projects/block_hosts/block.py --unblock
    
    

    