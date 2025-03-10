#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

version_greater_equal() {
    IFS='.' read -r -a local_version_parts <<< "$1"
    IFS='.' read -r -a latest_version_parts <<< "$2"

    for ((i=0; i<${#local_version_parts[@]}; i++)); do
        if [[ -z ${latest_version_parts[i]} ]]; then
            latest_version_parts[i]=0
        fi

        if ((10#${local_version_parts[i]} > 10#${latest_version_parts[i]})); then
            return 0
        elif ((10#${local_version_parts[i]} < 10#${latest_version_parts[i]})); then
            return 1
        fi
    done

    return 0
}

check_version() {
    local_version=$(cat $LOCALVERSION)
    latest_version=$(curl -s $LATESTVERSION)
    latest_changelog=$(curl -s $LASTESTCHANGE)

    
  if version_greater_equal "$local_version" "$latest_version"; then
    echo "Panel Version: $local_version"
  else
    echo "Panel Version: $local_version"
    echo "Latest Version: $latest_version"
    echo "${yellow}$latest_version Version Change Log:"
    echo "$latest_changelog"
  fi
}

show_version() {

    local_version=$(cat "$LOCALVERSION")
    echo "Panel Version: $local_version"

}


if [ "$1" == "check-version" ]; then
  check_version
elif [ "$1" == "show-version" ]; then
  show_version
else
  echo "Usage: $0 [check|show]" >&2
  exit 1
fi

exit 0