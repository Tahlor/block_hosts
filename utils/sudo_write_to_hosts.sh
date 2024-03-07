#!/bin/bash

# Check if we have exactly one argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 'new_hosts_content'"
    exit 1
fi

# Use `echo` and a heredoc to replace the content of /etc/hosts
# Note: This script must be run with sudo privileges to modify /etc/hosts
echo "$1" | sudo tee /etc/hosts > /dev/null
