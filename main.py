from flask import Flask, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, Commentform
from flask_gravatar import Gravatar
from functools import wraps
from flask import abort
import smtplib



my_gmail = "divya2pythondeveloper@gmail.com"
my_password = "xfnleymkhjcjmqkb"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager = LoginManager(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##RELATIONAL DATABASE
base = declarative_base()

##GRAVATAR IMAGES
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##USERLOADER FUNCTION
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    """The posts acts like a list of post created by a author"""
    posts = relationship('BlogPost', back_populates="author")  # child
    comment = relationship('Comment', back_populates="comment_author")


db.create_all()


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # author_id is foreign key
    author = relationship('User', back_populates="posts")  # parent
    comment = relationship('Comment', back_populates="parent_posts")  # parent


db.create_all()


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_author = relationship('User', back_populates="comment")

    blog_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_posts = relationship('BlogPost', back_populates="comment")

    # timestamp= db.Column(db.DateTime)


db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            flash("This Email already exists, Try to login!!")
            return redirect(url_for('register'))

        new_user = User(email=form.email.data,
                        name=form.name.data,
                        password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8))

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email Doesnot exist, Please check your data")
            return redirect(url_for('login'))
        if not check_password_hash(user.password, password):
            flash("Incorrect Password, Check again!")
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    form = Commentform()
    comment = Comment.query.filter_by(blog_id=post_id).order_by(Comment.id.desc())
    # comment = Comment.query.filter_by(blog_id=post_id).order_by(Comment.timestamp.desc())  # reset the blog.db
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Login to Comment below")
            return redirect(url_for('login'))
        comment = form.comment_body.data
        new_comment = Comment(body=comment,
                              comment_author=current_user,
                              parent_posts=requested_post)
        db.session.add(new_comment)
        db.session.commit()


    form.comment_body.data = ""
    return render_template("post.html", post=requested_post, ckform=form, current_user=current_user, comments=comment)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/contact', methods=['POST','GET'])
def contactpage():
    post_method =request.method
    data= request.form
    if post_method == "POST":
        send_email(data['user_name'],data['user_email'], data['user_phone'], data['user_msg'])
        return render_template('contact.html', msg_sent=True)
    else:
        return render_template('contact.html', msg_sent=False )
def send_email(first_name, last_name, phone , message):
    with smtplib.SMTP("smtp.gmail.com") as connection:

        connection.starttls()
        connection.login(user=my_gmail, password=my_password)
        connection.sendmail(from_addr=my_gmail,
                            to_addrs="divya4shivalaya@gmail.com",
                            msg=f"Subject:Contact form HTML FORM !\n\n"
                                f"Hi this is message from {first_name}{last_name}\n"
                                f"say hi\n"
                                f"This is my number {phone}\n"
                                f"{message}"
                            )



@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["POST", "GET"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        # author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        # post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>", methods=["POST", "GET"])
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='192.168.68.148', port=5000, debug=True)
