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
    
    

    
