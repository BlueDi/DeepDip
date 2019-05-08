#!/bin/sh

if [ "$#" -eq 0 ]; then
	echo "Starting parlance server without arguments..."
else
	echo "Starting parlancer server with arguments '$@'..."
fi

cd "$(dirname "$0")"
pipenv run parlance-server $@

