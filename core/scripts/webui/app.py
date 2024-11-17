import re
from flask import flash, request, redirect, session, render_template, Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import bcrypt
import json
from datetime import datetime, timedelta
from process import run_cli_command, COMMANDS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'ATGE7hyJpcIOnMhrzJ5CaVM0POeEoqHxOplxm6p6IzkMkkxbufkzbz348cd9sUKe'
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, email, password, is_admin=False):
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.is_admin = is_admin

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


with app.app_context():
    db.create_all()

def admin_exists():
    return User.query.filter_by(is_admin=True).first() is not None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    return render_template('login.html', admin_exists=admin_exists())


@app.route('/register', methods=['GET', 'POST'])
def register():
    if admin_exists():
        return redirect('/login') 

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        new_user = User(email=email, password=password, is_admin=True)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            return render_template('login.html', error='Email and password cannot be empty', admin_exists=admin_exists())

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return render_template('login.html', error='Invalid email format', admin_exists=admin_exists())

        if len(password) < 8 or not re.match("^[a-zA-Z0-9]+$", password):
            return render_template('login.html', error='Password must be at least 8 characters long and contain only letters and numbers', admin_exists=admin_exists())

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid email or password', admin_exists=admin_exists())

    return render_template('login.html', admin_exists=admin_exists())


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    user = User.query.filter_by(email=session['email']).first()
    server_info = run_cli_command(COMMANDS["server_info"])
    user_list_raw = run_cli_command(COMMANDS["list_users"])

    try:
        user_list = json.loads(user_list_raw)
    except json.JSONDecodeError:
        user_list = {"error": "Unable to parse user list"}

    for username, details in user_list.items():
        account_creation_date = datetime.strptime(details['account_creation_date'], "%Y-%m-%d")
        day_use = (datetime.now() - account_creation_date).days
        details['day_use'] = day_use
        details['download_bytes'] = details.get('download_bytes', 0)

        show_user_uri_output = run_cli_command(COMMANDS["show_user_uri"] + f" -u {username} -a")
        ipv4_match = re.search(r'IPv4:\s*(hy2://[^\s]+)', show_user_uri_output)
        ipv6_match = re.search(r'IPv6:\s*(hy2://[^\s]+)', show_user_uri_output)
        details['qr_data_ipv4'] = ipv4_match.group(1) if ipv4_match else None
        details['qr_data_ipv6'] = ipv6_match.group(1) if ipv6_match else None

    page = request.args.get('page', 1, type=int)
    per_page = 50
    total_users = len(user_list)
    total_pages = (total_users + per_page - 1) // per_page
    paginated_users = dict(list(user_list.items())[(page - 1) * per_page : page * per_page])

    return render_template('dashboard.html',
                           user=user,
                           server_info=server_info,
                           user_list=paginated_users,
                           page=page,
                           total_pages=total_pages)


@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    username = request.form.get('username')
    traffic_limit = request.form.get('traffic_limit')
    expiration_days = request.form.get('expiration_days')

    if not username or not traffic_limit or not expiration_days:
        flash('All fields are required to add a user.', 'error')
        return redirect(url_for('dashboard', tab='users'))

    add_user_command = f"{COMMANDS['add_user']} -u {username} -t {traffic_limit} -e {expiration_days}"
    add_user_result = run_cli_command(add_user_command)

    flash(f"User {username} added successfully!" if "success" in add_user_result else f"Error adding user: {add_user_result}", 
          'success' if "success" in add_user_result else 'error')

    return redirect(url_for('dashboard', tab='users'))


@app.route('/remove_user', methods=['POST'])
@login_required
def remove_user():
    username = request.form['username']
    remove_user_command = f"{COMMANDS['remove_user']} -u {username}"
    remove_user_result = run_cli_command(remove_user_command)

    flash(f"User {username} removed successfully!" if "success" in remove_user_result else f"Error: {remove_user_result}", 
          'success' if "success" in remove_user_result else 'error')

    return redirect(url_for('dashboard', tab='users'))

@app.route('/reset_user', methods=['POST'])
@login_required
def reset_user():

    username = request.form.get('username')
    if username:
        reset_command = COMMANDS["reset_user"].format(username=username)
        reset_output = run_cli_command(reset_command)
        flash(f'Reset user {username}: {reset_output}', 'success')
    else:
        flash('Username not provided', 'error')

    return redirect(url_for('dashboard', tab='users'))



@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9090)
