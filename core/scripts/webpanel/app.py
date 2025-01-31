import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from flask_paginate import Pagination, get_page_parameter
import json
from datetime import datetime, timedelta


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


CLI_SCRIPT_PATH = "/etc/hysteria/core/cli.py"

def get_server_info():
    cli_output = run_cli_command("server-info")
    extended_info = parse_cli_server_info(cli_output)
    return {
        "extended": extended_info
    }

def parse_cli_server_info(cli_output):
    info = {}
    if cli_output:
        lines = cli_output.splitlines()
        for line in lines:
            if "CPU Usage" in line:
                info["cpu_usage_cli"] = line.split(":")[1].strip()
            elif "Total RAM" in line:
                info["total_ram"] = line.split(":")[1].strip()
            elif "Used RAM" in line:
                info["used_ram"] = line.split(":")[1].strip()
            elif "Online Users" in line:
                info["online_users"] = line.split(":")[1].strip()
            elif "uploaded" in line:
                info["upload_traffic"] = line.split("🔼")[1].split(" ")[0].strip()
            elif "downloaded" in line:
                info["download_traffic"] = line.split("🔽")[1].split(" ")[0].strip()
            elif "total traffic" in line:
                info["total_traffic"] = line.split("📊")[1].split(" ")[1].strip()
    return info

def run_cli_command(*args):
    try:
        process = subprocess.run(
            ["python3", CLI_SCRIPT_PATH] + list(args),
            capture_output=True,
            text=True,
            check=True,
        )
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running CLI command: {e}")
        print(f"stderr: {e.stderr}")
        return None

# --- Routes ---

@app.route("/")
def index():
    if not is_logged_in():
        return redirect(url_for("login"))

    return render_template("index.html")

@app.route("/get_server_info")
def get_server_info_route():
    server_info = get_server_info()
    return jsonify(server_info)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == os.environ.get("ADMIN_USERNAME") and \
           password == os.environ.get("ADMIN_PASSWORD"):
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/users")
def users():
    if not is_logged_in():
        return redirect(url_for("login"))

    user_list_str = run_cli_command("list-users")
    users = []

    if user_list_str:
        try:
            user_data_all = json.loads(user_list_str)
            for username, user_data in user_data_all.items():
                download_bytes = user_data.get("download_bytes", 0)
                upload_bytes = user_data.get("upload_bytes", 0)
                max_download_bytes = user_data.get("max_download_bytes", 0)

                traffic_used = format_traffic(download_bytes + upload_bytes)

                creation_date_str = user_data.get("account_creation_date")
                expiration_days = user_data.get("expiration_days")
                expiry_str = "N/A"

                if creation_date_str and expiration_days:
                    try:
                        creation_date = datetime.strptime(
                            creation_date_str, "%Y-%m-%d"
                        )
                        expiry_date = creation_date + timedelta(
                            days=expiration_days
                        )
                        expiry_str = expiry_date.strftime("%Y-%m-%d")
                    except ValueError:
                        print(
                            f"Error parsing date for user {username}: '{creation_date_str}'"
                        )

                user_configs = get_user_configs(username)

                user_info = {
                    "username": username,
                    "quota": format_traffic(max_download_bytes),
                    "traffic_used": traffic_used,
                    "expiry": expiry_str,
                    "expiry_days": user_data.get("expiration_days"),
                    "enable": "enabled"
                    if not user_data.get("blocked", False)
                    else "disabled",
                    "configs": user_configs,
                    "status": user_data.get("status", "Not Active")
                }
                users.append(user_info)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    # --- Pagination ---
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 20
    offset = (page - 1) * per_page

    total_users = len(users)
    pagination = Pagination(page=page, per_page=per_page, total=total_users, css_framework='bootstrap4')

    paginated_users = users[offset : offset + per_page]

    return render_template("users.html", users=paginated_users, pagination=pagination)


def get_user_configs(username):
    configs = []
    cli_output = run_cli_command("show-user-uri", "-u", username, "-asn")

    if cli_output:
        lines = cli_output.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("hy2://"):
                if "@" in line:
                    ip_version = "IPv6" if line.split("@")[1].count(":") > 1 else "IPv4"
                    config_type = ip_version
                    config_link = line
                else:
                    continue 
            elif line.startswith("https://"):
                if "singbox" in line.lower():
                    config_type = "Singbox"
                elif "normal" in line.lower():
                    config_type = "Normal-SUB"
                else:
                    continue
                config_link = line
            else:
                continue

            configs.append(
                {
                    "type": config_type,
                    "link": config_link,
                }
            )

    return configs

def format_traffic(traffic_bytes):
    if traffic_bytes < 1024:
        return f"{traffic_bytes} B"
    elif traffic_bytes < 1024**2:
        return f"{traffic_bytes / 1024:.2f} KB"
    elif traffic_bytes < 1024**3:
        return f"{traffic_bytes / 1024**2:.2f} MB"
    else:
        return f"{traffic_bytes / 1024**3:.2f} GB"

# --- User Management Routes ---
@app.route("/add_user", methods=["POST"])
def add_user():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    username = request.form.get("username")
    traffic_limit = request.form.get("traffic_limit")
    expiration_days = request.form.get("expiration_days")
    password = generate_password()
    creation_date = datetime.now().strftime('%Y-%m-%d')

    result = run_cli_command(
        "add-user",
        "--username",
        username,
        "--traffic-limit",
        traffic_limit,
        "--expiration-days",
        expiration_days,
        "--password",
        password,
        "--creation-date",
        creation_date,
    )

    if result:
        return jsonify({"message": "User added successfully"})
    else:
        return jsonify({"error": "Failed to add user"}), 500

@app.route("/edit_user", methods=["POST"])
def edit_user():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    username = request.form.get("username")
    new_username = request.form.get("new_username")
    new_traffic_limit = request.form.get("new_traffic_limit")
    new_expiration_days = request.form.get("new_expiration_days")
    blocked = request.form.get("blocked") == "true"

    command_args = [
        "edit-user",
        "--username", username
    ]
    if new_username:
        command_args.extend(["--new-username", new_username])
    if new_traffic_limit:
        command_args.extend(["--new-traffic-limit", new_traffic_limit])
    if new_expiration_days:
        command_args.extend(["--new-expiration-days", new_expiration_days])
    if blocked:
        command_args.append("--blocked")

    result = run_cli_command(*command_args)

    if result and "User updated successfully." in result:
          return "User updated successfully"
    else:
        return jsonify({"error": "Failed to update user"}), 500

@app.route("/delete_user", methods=["POST"])
def delete_user():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    username = request.form.get("username")

    result = run_cli_command("remove-user", "--username", username)

    if result:
        return jsonify({"message": "User deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete user"}), 500
    
def generate_password() -> str:
    return subprocess.check_output(['pwgen', '-s', '32', '1'], shell=False).decode().strip()

@app.route("/reset_user", methods=["POST"])
def reset_user():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    username = request.form.get("username")

    result = run_cli_command("reset-user", "--username", username)

    if result:
        return jsonify({"message": "User reset successfully"})
    else:
        return jsonify({"error": "Failed to reset user"}), 500

def is_logged_in():
    return "logged_in" in session

if __name__ == "__main__":
    app.run(debug=True)