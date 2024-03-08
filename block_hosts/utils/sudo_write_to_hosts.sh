#!/bin/bash
path=${2:-/etc/hosts}
# Check if we have exactly one argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 'new_hosts_content'"
    exit 1
fi

echo "$1" | sudo tee $path > /dev/null