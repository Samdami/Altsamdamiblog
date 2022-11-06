from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin, current_user
import os

base_dir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(base_dir, 'my_login.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = '5e0b18fd5de07e49f80cb4f8'

"""
To get a 12-digit (any number of choice) secret key, run this in the terminal:

python
import secrets
secrets.token_hex(12)
exit()

Copy the token from the terminal and paste it as the secret key in app.config above
"""

db = SQLAlchemy(app)
login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    """This is the User database model"""
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=False)
   

    def __repr__(self):
        return f"User <{self.username}>"

class BlogPost(db.Model):
    """This is the blogpost database model"""
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(50))
    subtitle = db.Column(db.String(50))
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.Text)
    author = db.Column(db.Text)
   

@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    return render_template('index.html', posts=BlogPost.query.all())

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/post/<int:post_id>')
def post(post_id):
    try:
        post = BlogPost.query.filter_by(id=post_id).one()
    except:
        return render_template('404.html')
    date_posted = post.date_posted.strftime('%B %d, %Y')
    if current_user.is_authenticated and current_user.username == post.author:
        return render_template('post.html', post=post, date_posted=date_posted, user_owns_post=True)
    else:
        return render_template('post.html', post=post, date_posted=date_posted, user_owns_post=False)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/add')
def add():
    if current_user.is_authenticated:
        return render_template('add.html')
    else:
        return redirect(url_for('login'))

@app.route('/post_deleted')
def post_deleted():
    """Notifies a user whether the delete operation was successful or not"""
    return render_template('post_deleted.html')

@app.route('/posts/<int:post_id>/delete')
def delete(post_id):
    post_to_be_del = BlogPost.query.filter_by(id=post_id).one()
    if current_user.is_authenticated and current_user.username == post_to_be_del.author:
        BlogPost.query.filter_by(id=post_id).delete()
        db.session.commit()
        return redirect(url_for('post_deleted'))
    else:
        return redirect(url_for('login'))

@app.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    post_to_be_edited = BlogPost.query.filter_by(id=post_id).one()
    if current_user.is_authenticated and current_user.username == post_to_be_edited.author:
        if request.method == 'GET':
            return render_template('edit_post.html', post=post_to_be_edited)
        elif request.method == 'POST':
            post_to_be_edited.title = request.form['title']
            post_to_be_edited.subtitle = request.form['subtitle']
            post_to_be_edited.content = request.form['content']
            db.session.commit()
            return redirect(url_for('post', post_id=post_id))
    else:
        return redirect(url_for('login'))

@app.route('/addpost', methods=['POST'])
def addpost():
    title = request.form['title']
    subtitle = request.form['subtitle']
    content = request.form['content']
    author = current_user.username

    post = BlogPost(title=title, subtitle=subtitle, content=content, author=author, date_posted=datetime.now())

    db.session.add(post)
    db.session.commit()
    
    return redirect(url_for('index'))

          


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error_msg="Invalid username or password. Try again.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user() 
    return redirect(url_for('login'))


@app.route('/protected')
@login_required
def protected():
    return render_template('protected.html')


@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        passwords_no_match = ""

        if confirm != password:
            passwords_no_match = "The two passwords must match"

        username_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()

        if username_exists or email_exists or passwords_no_match:
            username_msg = "This Username is already being used by another user."
            email_msg = "This Email is already being used by another user."
            return render_template('signup.html', username_error=username_msg, email_error=email_msg, password_error=passwords_no_match)
        password_hash = generate_password_hash(password)

        new_user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)