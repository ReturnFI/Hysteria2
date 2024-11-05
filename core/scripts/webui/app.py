import re
from flask import flash, request, redirect, session, render_template, Flask, url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import json
from datetime import datetime
from process import run_cli_command, COMMANDS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'm7fZJgadC6zenScAVDF28F50'


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
            print(f"User {user.email} logged in, session set") 
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid email or password', admin_exists=admin_exists())

    return render_template('login.html', admin_exists=admin_exists())


@app.route('/dashboard')
def dashboard():
    if 'email' in session:
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
                                total_pages=total_pages
                                )
    
    return redirect('/login')

@app.route('/reset_user', methods=['POST'])
def reset_user():
    if 'email' not in session:
        return redirect('/login')
    
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
    session.pop('is_admin', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9090)
