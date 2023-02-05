#!/bin/bash

app_name="fetch-etl-server"
pid_file="pid_file.pid"

get_pid() {
	cat "$pid_file"
}

is_running() {
	[ -f "$pid_file" ] && ps `get_pid` > /dev/null 2>&1
}


if is_running; then
	echo -n "Stopping $app_name.."
	kill `get_pid`
	for i in {1..10}
	do
		if ! is_running; then
			break
		fi
		
		echo -n "."
		sleep 1
	done
	echo
	
	if is_running; then
		echo "Not stopped; may still be shutting down or shutdown may have failed"
		exit 1
	else
		echo "Stopped"
		if [ -f "$pid_file" ]; then
			rm "$pid_file"
		fi
	fi
else
	echo "Not running"
fi