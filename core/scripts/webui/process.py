# process.py
import subprocess
import shlex

CLI_PATH = '/etc/hysteria/core/cli.py'

COMMANDS = {
    "server_info": f"python3 {CLI_PATH} server-info",
    "list_users": f"python3 {CLI_PATH} list-users",
    "add_user": f"python3 {CLI_PATH} add-user -u {{username}} -t {{traffic_limit}} -e {{expiration_days}}",
    "get_user": f"python3 {CLI_PATH} get-user -u {{actual_username}}",
    "reset_user": f"python3 {CLI_PATH} reset-user -u {{username}}"
}

def run_cli_command(command):
    try:
        args = shlex.split(command)
        result = subprocess.check_output(args, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        return f'Error: {e.output.decode("utf-8")}'
