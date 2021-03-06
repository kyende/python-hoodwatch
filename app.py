from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hoodwatch'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)



# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# ContactTracing
@app.route('/recent_breakings')
def breakings():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get reported recent_breakings
    result = cur.execute("SELECT * FROM reported_breakings")

    breakings = cur.fetchall()

    if result > 0:
        return render_template('breakings.html', breakings=breakings)
    else:
        msg = 'No Responses Captured'
        return render_template('breakings.html', msg=msg)
    # Close connection
    cur.close()



#Single contact tracing Response
@app.route('/reported_breakings/<string:id>/')
def breakings(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Breakings Record
    result = cur.execute("SELECT * FROM reported_breakings WHERE id = %s", [id])

    breakings = cur.fetchone()

    return render_template('breaking.html', breakings=breakings)



# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM reported_breakings WHERE name = %s", [session['username']])
    Responses = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', Responses=Responses)
    else:
        msg = 'No Breakings Reported'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

#  form
class ArticleForm(Form):
    name= StringField('Full Name', [validators.Length(min=1, max=200)])
    address  = StringField('Hood Address', [validators.length(min=1, max=200)])
    description = StringField('Breaking Description',[validators.length(min=1,max=15)])

# Add report Breaking
@app.route('/report_breaking', methods=['GET', 'POST'])
@is_logged_in
def add_question():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        address = form.address.data
        description = form.description.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO reported_breakings(name, address, description) VALUES(%s, %s, %s)", (session['username'], address, description))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Crime Response Submitted', 'success')

        return redirect(url_for('dashboard'))

    return render_template('report_breaking.html', form=form)



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
