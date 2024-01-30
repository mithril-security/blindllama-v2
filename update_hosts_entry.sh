#!/bin/bash

# Check if the script is run as root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (sudo)."
  exit 1
fi

# Check for the correct number of arguments
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <public_ip> <domain_name>"
  exit 1
fi

public_ip="$1"
domain_name="$2"
hosts_file="/etc/hosts"

# Create a temporary file
temp_file=$(mktemp)

# Use sed to update the temporary file, matching domain_name exactly
sed -E "/^[^[:space:]]+[[:space:]]+$domain_name[[:space:]]*$/d" "$hosts_file" > "$temp_file" # Remove any existing entry for domain_name
echo "$public_ip $domain_name" >> "$temp_file"                                             # Add the new entry

# Use cat to overwrite the /etc/hosts file
cat "$temp_file" > "$hosts_file"

# Remove the temporary file
rm "$temp_file"

echo "Entry added or updated in /etc/hosts:"
grep " $domain_name" "$hosts_file"