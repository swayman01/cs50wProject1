import os, functools, requests, json

from flask import Flask, session, render_template, request, g
from flask import Blueprint, flash, g, redirect, url_for
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
engine = create_engine('postgres://swuklgswqdvenp:3362f809de63cc65ad1f87c891fe7ab68da19a6738f01a3e80e866c0f799a8cf@ec2-50-16-196-57.compute-1.amazonaws.com:5432/dcevpu14st78ms')
from werkzeug.security import check_password_hash, generate_password_hash
app = Flask(__name__)
# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"]='dev'

# Check for environment variable
#export DATABASE_URL=postgres://swuklgswqdvenp:3362f809de63cc65ad1f87c891fe7ab68da19a6738f01a3e80e866c0f799a8cf@ec2-50-16-196-57.compute-1.amazonaws.com:5432/dcevpu14st78ms
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# from flaskr.db import get_db
bp = Blueprint('auth', __name__, url_prefix='/auth')
Session(app)

global currentisbn
currentisbn="-1"
#  __init__.py from flaskr Tutorial
def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    # register the database commands
    from flaskr import db
    db.init_app(app)
    # apply the blueprints to the app
    from flaskr import auth, blog
    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule('/', endpoint='index')

    return app
#end from flaskr

# Set up database

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
error=""
#isbn = "-1" #Attempt to make global failed
def get_isbn():
    gisbn = getattr(g, '_gisbn', None)
    if gisbn is None:
        g.gisbn = ""

def add_isbn(gisbn):
    setattr(g, '_gisbn', gisbn)
    return gisbn

@app.route("/", methods=['GET', 'POST'])
def index():
    g.user = "Line_42"
    subtitle="Home Page"
    return render_template("index.html",subtitle=subtitle, error=error)


@app.route("/registration",methods=['POST','GET'])
def Registration():
    subtitle="Registration Page"
    users = db.execute("SELECT * FROM user_rev1").fetchall()
    #Initiate Variables
    user="TBD"
    password="TBD"
    error = 'Default'
    return render_template("users.html",subtitle=subtitle, error=error, users=users)


@app.route("/register",methods=['POST','GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password=generate_password_hash(password)
    users= db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
    try:
        username=users.username
        error = 'User {} is already registered.'.format(username)
        subtitle='User {} is already registered.'.format(username)
        session['user_id'] = users['id']
        return render_template("index.html", subtitle=subtitle, users=users,
        username=username,error=RuntimeError)
    except:
        db.execute("INSERT INTO user_rev1 (username, password) VALUES (:username, :password)",
        {"username": username, "password": password})
        db.commit()
        subtitle='Successfully registered {}.'.format(username)
        users= db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
        session['user_id'] = users['id']
        return render_template("search.html",subtitle=subtitle,error=session['user_id'])


@app.route("/login",methods=['POST','GET'])
def login():
    subtitle= "Login Page"
    # error = g.user #doesn't carryover from index
    return render_template("users.html",subtitle=subtitle, error=error)


@app.route("/loginuser",methods=['POST','GET'])
def loginuser():
    subtitle="loginuser"
    error="none"
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    try:
        user = db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
        if user is None:
            error = 'Incorrect username.'
            return render_template("index.html", subtitle=subtitle, users=username,
                    username=username,error=error)
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'
            return render_template("index.html", subtitle=subtitle, user=username,
                    username=username,error=error)
    except:
        return render_template("index.html", subtitle=subtitle, users=username,
                username=username,error="Error in retrieving data(line 161)")
    session.clear()
    session['user_id'] = user['id']
    g.user = db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
    return render_template("search.html",subtitle=subtitle,error="")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        subtitle="login_required"
        try:
            error=session['user_id']
            if session['user_id'] < 1:
                return render_template("index.html", subtitle=subtitle, error=error)
        except:
            subtitle = "Nice Try"
            error = "Please log in"
            return render_template("index.html", subtitle=subtitle, error=error)
        return view(**kwargs)
    return wrapped_view


@app.route("/search",methods=['POST','GET'])
@login_required
def search():
    subtitle="Line 188: search.html from route"
    try:
        return render_template("search.html",subtitle=subtitle,error=session['user_id'])
    except:
        error="186: User Logged Out"
        return render_template("index.html", subtitle=subtitle, error=error)


@app.route("/books",methods=['POST','GET'])
@login_required
def books():
    global currentisbn
    subtitle="Book Listing"
    error=""
    isbn = ""
    title = ""
    author = ""
    if request.method == 'POST':
        try:
            isbn = request.form['isbn']
            title = request.form['title']
            author = request.form['author']
            bookct = 0
            books = db.execute("SELECT * FROM books WHERE books.isbn = :isbn", {"isbn": isbn})
            for book in books:
                bookct += 1
            if bookct>=1:
                #return "line 220"  - This path is followed with ISBN
                #return books with matching ISBN, assume ISBN is unique
                error = "ISBN Search"
                books = db.execute("SELECT * FROM books WHERE books.isbn = :isbn", {"isbn": isbn}).fetchall()
                #currentisbn=[]
                for book in books:
                     #currentisbn.append(book[1])
                     currentisbn=book[1]
                return render_template("books.html", subtitle=subtitle, error=error,
                isbn=str(isbn), books=books)
            if bookct <1:
                # Try title
                books = db.execute("SELECT * FROM books WHERE books.title LIKE :title", {"title": title})
                bookct = 0
                #currentisbn=[]
                for book in books:
                    bookct += 1
                    #currentisbn.append(book[1])
                    currentisbn=book[1]
                if bookct >= 1:
                    #return books with matching title
                    books = db.execute("SELECT * FROM books WHERE books.title LIKE :title", {"title": title})
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn,
                    title=title, author=author, books=books,currentisbn=currentisbn)
                if bookct <1:
                    #Try author
                    books = db.execute("SELECT * FROM books WHERE books.author LIKE :author", {"author": author})
                    bookct = 0
                    #currentisbn=[]
                    for book in books:
                        bookct += 1
                        #currentisbn.append(book[1])
                        currentisbn=book[1]
                    if bookct >= 1:
                        #return books with matching author
                        books = db.execute("SELECT * FROM books WHERE books.author LIKE :author", {"author": author})
                        i=0
                        error = "matched author"
                        return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn,
                        title=title, author=author, books=books, currentisbn=currentisbn, bookct=bookct)
                    else:
                        # No books found
                        subtitle = "No Books Found"
                        return render_template("search.html", subtitle=subtitle, error=error, isbn=isbn,
                        title=title, author=author, books=books,i=i)

        except:
            subtitle = "Error in Seach Form"
            i=0
            render_template("books.html", subtitle=subtitle, error=error, isbn=isbn,
            title=title, author=author, books=books, currentisbn=currentisbn, bookct=bookct,i=i)
            #return render_template("search.html", subtitle=subtitle, error=error, isbn=isbn,
            #title=title, author=author, book=book)

@app.route("/bookpage",methods=['POST','GET'])
@login_required
def bookpage():
    subtitle="Book page"
    global currentisbn
    user=session['user_id']
    isbn = request.form['bookisbn']
    currentisbn=isbn
    #return currentisbn #currentisbn is set here
    res = requests.get("https://www.goodreads.com/book/review_counts.json", \
    params={"key": " hj7IlmJs5Em6ojWbiZy8A", "isbns": isbn})
    data_json = res.json()
    books_json = data_json['books']
    nratings = books_json[0]['work_ratings_count']
    avgrating = books_json[0]['average_rating']
    books = db.execute("SELECT * FROM books WHERE books.isbn = :isbn", {"isbn": isbn}).fetchone()
    book_reviewed = False
    reviews = db.execute("SELECT user_id, username, num_stars, review \
        FROM user_rev1 RIGHT JOIN reviews ON reviews.user_id = user_rev1.id \
        WHERE reviews.book_id=:isbn", {"isbn": isbn}).fetchall()
    revcount = 0
    for review in reviews:
        revcount +=1
        if review.user_id == session['user_id']:
            book_reviewed = True
    error = book_reviewed
    title=books.title
    author=books.author
    # return render_template("bookpage.html", subtitle=subtitle, isbn=isbn,
    # books=books, nratings=nratings, avgrating=avgrating,
    # title=title, author=author, error=error, book_reviewed=book_reviewed,
    # reviews=reviews, revcount=revcount, user=user)
    if request.method == 'POST':
        try:
            return render_template("bookpage.html", subtitle=subtitle, isbn=isbn,
            books=books, nratings=nratings, avgrating=avgrating,
            title=title, author=author, error=error, book_reviewed=book_reviewed,
            reviews=reviews, revcount=revcount, user=user)
        except:
            error = "Error in bookpage"
            #return render_template("search.html", subtitle=subtitle, error=error)
            return render_template("bookpage.html", subtitle=subtitle, error=error, isbn=isbn,
            title=title, author=author, books=books)
    else:
        error = "line 260 error in request.method == 'POST'"
        return render_template("bookpage.html", subtitle=subtitle, error=error, book=book)

#Delete when done
@app.route("/submitreviewtest",methods=['POST','GET'])
@login_required
def submitreviewtest():
    subtitle="Submit review tests"
    global currentisbn
    isbn=str(currentisbn)
    book_reviewed = False
    return render_template("submitreview.html", subtitle=subtitle)


@app.route('/submitreview',methods=['POST','GET'])
@login_required
def submitreview():
    subtitle="Your Review"
    global currentisbn #currentisbn not set here
    isbn=currentisbn
    user=session['user_id']
    res = requests.get("https://www.goodreads.com/book/review_counts.json", \
    params={"key": " hj7IlmJs5Em6ojWbiZy8A", "isbns": isbn})
    data_json = res.json()
    books_json = data_json['books']
    nratings = books_json[0]['work_ratings_count']
    avgrating = books_json[0]['average_rating']
    books = db.execute("SELECT * FROM books WHERE books.isbn = :isbn", {"isbn": isbn}).fetchone()
    book_reviewed = False
    reviews = db.execute("SELECT user_id, username, num_stars, review \
        FROM user_rev1 RIGHT JOIN reviews ON reviews.user_id = user_rev1.id \
        WHERE reviews.book_id=:isbn", {"isbn": isbn}).fetchall()
    revcount = 0
    for review in reviews:
        revcount +=1
        if review.user_id == session['user_id']:
            book_reviewed = True
    error = book_reviewed
    title=books.title
    author=books.author
    book_reviewed = False
    if request.method == 'POST':
        number_stars = -1
        #TODO add checks to see if review exists, if so, post
        #TODO Allow rewrite of review
        #TODO try: for no goodreads data
        book_id=currentisbn
        user_id=session['user_id']
        review = request.form['reviewtext']
        #TODO Add Logic for no stars - Fade Submit Button
        num_stars = request.form['options']
        reviewtext = request.form['reviewtext']
        nstars = request.form['options']
        error="Error in render template line ~316"
        db.execute("INSERT INTO reviews (user_id, book_id, num_stars, review) \
        VALUES (:user_id, :book_id, :num_stars, :review)",
        {"user_id": user_id, "book_id": book_id, "num_stars": num_stars, "review": review})
        #db.commit()TODO Uncomment
        reviews = db.execute("SELECT user_id, username, num_stars, review \
            FROM user_rev1 RIGHT JOIN reviews ON reviews.user_id = user_rev1.id \
            WHERE reviews.book_id=:isbn", {"isbn": isbn}).fetchall()
        r = db.execute("SELECT user_id, username, num_stars, review \
            FROM user_rev1 RIGHT JOIN reviews ON reviews.user_id = user_rev1.id \
            WHERE reviews.book_id=:isbn", {"isbn": isbn}).fetchone()

        revcount = 0
        for review in reviews:
            revcount +=1
            if review.user_id == session['user_id']:
                book_reviewed = True
        error = book_reviewed
        #title="Add title"
        #title=books.title
        #author="Add author"
        #author=books.author
        nratings="add nratings"
        avgrating="avgrating"
        user="add user"
        res = requests.get("https://www.goodreads.com/book/review_counts.json", \
        params={"key": " hj7IlmJs5Em6ojWbiZy8A", "isbns": isbn})
        data_json = res.json()
        books_json = data_json['books']
        nratings = books_json[0]['work_ratings_count']
        avgrating = books_json[0]['average_rating']
        #return render_template("submitreview.html", subtitle=subtitle)
        #stuff below works
        return render_template("bookpage.html", subtitle=subtitle, isbn=isbn,
        books=books, nratings=nratings, avgrating=avgrating,
        title=title, author=author, error=error, book_reviewed=book_reviewed,
        reviews=reviews, revcount=revcount, user=user)
        #end of what works
        try:
            return render_template("submitreview.html", subtitle=subtitle,
                number_stars=number_stars, reviewtext=reviewtext, nstars=nstars)
        except:
            return error


@app.route("/test",methods=['POST','GET'])
@login_required
def test():
    subtitle="Search for Books"
    error=""
    # ISBN = request.form['ISBN']
    # title = "hardcoded title"
    #return render_template("test.html", subtitle=subtitle, error=error,
           #ISBN=ISBN, title=title)
    if request.method == 'POST':
        isbn = request.form['isbn']
        title = request.form['title']
        author = request.form['author']
        return render_template("test.html", subtitle=subtitle, error=error, isbn=isbn,
        title=title, author=author)
    subtitle="Line 223: Not if request.method == 'POST':"
    return render_template("test.html", subtitle=subtitle, error=error)


#Logout from Flask tutorial
@app.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    subtitle="Logged Out"
    error=""
    return render_template("index.html", subtitle=subtitle, error=error)

#decorators from Flask Tutorial
#Not sure this is needed
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        # g.user = get_db().execute(
        #     'SELECT * FROM user WHERE id = ?', (user_id,)
        # ).fetchone()
        g.user = db.execute("SELECT * FROM user_rev1 WHERE user_rev1.id = :user_id", {"username": user_id}).fetchone()
