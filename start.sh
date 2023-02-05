#!/bin/bash
app_name="fetch-etl-server"
pid_file="pid_file.pid"
cmd="python3 -u $app_name.py"

get_pid() {
	cat "$pid_file"
}

is_running() {
	[ -f "$pid_file" ] && ps `get_pid` > /dev/null 2>&1
}

is_installed(){
	[ -d venv ]
}

if is_running; then
	echo "Already started"
else
	if is_installed; then
		source venv/bin/activate
		echo "Starting $app_name"
		nohup $cmd &
		echo $! > "$pid_file"
		echo "Started $app_name"
		deactivate
		if ! is_running; then
			echo "Unable to start, see $app_log and $err_log"
			exit 1
		fi
	else
		echo "Run the activate.sh script to install required modules before starting"
	fi
fi