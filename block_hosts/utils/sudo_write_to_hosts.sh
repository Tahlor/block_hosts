#!/bin/bash

# Path to hosts file, default is /etc/hosts
path=${2:-/etc/hosts}

# Check if exactly one argument is provided
if [ "$#" -ne 1 ] && [ "$#" -ne 2 ]; then
    echo "Usage: $0 'new_hosts_content_path'"
    exit 1
fi

# Use the content of the file provided as first argument
sudo tee $path < "$1" > /dev/null
