import os, functools, requests, json

from flask import Flask, session, render_template, request, g
from flask import Blueprint, flash, g, redirect, url_for
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text, select, bindparam
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
bp = Blueprint('auth', __name__, url_prefix='/auth')
Session(app)
# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
sql_session = sessionmaker()
error=""
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


@app.route("/", methods=['GET', 'POST'])
def index():
    g.user = "Line_42"
    subtitle="Home Page"
    return render_template("index.html",subtitle=subtitle, error=error)


@app.route("/registration",methods=['POST','GET'])
def Registration():
    subtitle="Registration Page"
    users = db.execute("SELECT * FROM user_rev1").fetchall()
    #Initiate Variables to prevent web crash
    user="TBD"
    password="TBD"
    error = ""
    return render_template("users.html",subtitle=subtitle, error=error, users=users)


@app.route("/register",methods=['POST','GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password=generate_password_hash(password)
        error = "" 
    try:
        users= db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
        username=users.username
        subtitle='User {} is already registered.'.format(username)
        session['user_id'] = users['id']
        return render_template("index.html", subtitle=subtitle, users=users,
        username=username,error=error)
    except:
        db.execute("INSERT INTO user_rev1 (username, password) VALUES (:username, :password)",
        {"username": username, "password": password})
        db.commit()
        subtitle='Successfully registered {}'.format(username)
        users= db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
        session['user_id'] = users['id']
        error = ""
        return render_template("search.html",subtitle=subtitle,error=error)


@app.route("/login",methods=['POST','GET'])
def login():
    subtitle= "Login Page"
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
                username=username,error="Error in retrieving data(line 165)")
    session.clear()
    session['user_id'] = user['id']
    g.user = db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
    return render_template("search.html",subtitle=subtitle,error="")


def login_required(view):
    #View decorator that redirects anonymous users to the login page.
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        subtitle="login_required"
        try:
            error = session['user_id']
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
    subtitle=""
    try:
        return render_template("search.html",subtitle=subtitle,error="")
    except:
        error="186: User Logged Out"
        return render_template("index.html", subtitle=subtitle, error=error)


@app.route("/books",methods=['POST','GET'])
@login_required
def books():
    """Philosophy:
       If only one field is filled out search on that field
       Use AND when searching multiple fields """
    #SOMEDAY: Find way to reduce duplicate code
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
            isbnsearch = str(isbn+"%")
            titlesearch = str(title+"%")
            authorsearch = str(author+"%")
            if isbnsearch == "%" and titlesearch == "%" and authorsearch == "%":
                #SOMEDAY Add Alerts
                # flash ("The form is blank. Please fill-in at least one field")
                subtitle = "The form is blank"
                error = "Please fill-in at least one field"
                return render_template("search.html", subtitle=subtitle, error=error)
            #Start with one search item
            #ISBN only
            if isbnsearch != "%" and titlesearch == "%" and authorsearch == "%":
                books_ret = db.execute("SELECT * FROM books \
                   WHERE books.isbn LIKE :isbnsearch LIMIT 50", {"isbnsearch": isbnsearch}).fetchall()
                bookct = 0
                for book in books_ret:
                    bookct += 1
                if bookct>=1:
                    subtitle = "ISBN Search"
                    if bookct > 49:
                        error = "Try a more restricted search. Search limited to the first 50 entries."
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn, books=books_ret)
                if bookct <1:
                    error = "No books found with this ISBN"
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn)
            #Title only
            if isbnsearch == "%" and titlesearch != "%" and authorsearch == "%":
                books_ret = db.execute("SELECT * FROM books \
                   WHERE books.title LIKE :titlesearch LIMIT 50", {"titlesearch": titlesearch}).fetchall()
                bookct = 0
                for book in books_ret:
                    bookct += 1
                if bookct>=1:
                    subtitle = "Title Search"
                    if bookct > 49:
                        error = "Try a more restricted search. Search limited to the first 50 entries."
                    return render_template("books.html", subtitle=subtitle, error=error, title=title, books=books_ret)
                if bookct <1:
                    error = "No books found with this title"
                    return render_template("books.html", subtitle=subtitle, error=error, title=title)
            #Author only
            if isbnsearch == "%" and titlesearch == "%" and authorsearch != "%":
                books_ret = db.execute("SELECT * FROM books \
                   WHERE books.author LIKE :authorsearch LIMIT 50", {"authorsearch": authorsearch}).fetchall()
                bookct = 0
                for book in books_ret:
                    bookct += 1
                if bookct>=1:
                    subtitle = "Author Search"
                    if bookct > 49:
                        error = "Try a more restricted search. Search limited to the first 50 entries."
                    return render_template("books.html", subtitle=subtitle, error=error, author=author, books=books_ret)
                if bookct <1:
                    error = "No books found with this author"
                    return render_template("books.html", subtitle=subtitle, error=error, author=author)
            #Title and Author
            if isbnsearch == "%" and titlesearch != "%" and authorsearch != "%":
                books_ret = db.execute("SELECT * FROM books \
                   WHERE books.title LIKE :titlesearch AND books.author LIKE :authorsearch LIMIT 50", \
                   {"titlesearch": titlesearch,"authorsearch": authorsearch}).fetchall()
                bookct = 0
                for book in books_ret:
                    bookct += 1
                if bookct>=1:
                    subtitle = "Title and Author Search"
                    if bookct > 49:
                        error = "Try a more restricted search. Search limited to the first 50 entries."
                    return render_template("books.html", subtitle=subtitle, error=error, title=title, author=author, books=books_ret)
                if bookct <1:
                    error = "No books found with this title and author"
                    return render_template("books.html", subtitle=subtitle, error=error, title=title, author=author)
            #ISBN and Title
            if isbnsearch != "%" and titlesearch != "%" and authorsearch == "%":
                books_ret = db.execute("SELECT * FROM books \
                   WHERE books.isbn LIKE :isbnsearch AND books.title LIKE :titlesearch LIMIT 50", \
                   {"isbnsearch": isbnsearch,"titlesearch": titlesearch}).fetchall()
                bookct = 0
                for book in books_ret:
                    bookct += 1
                if bookct>=1:
                    subtitle = "ISBN and Title Search"
                    if bookct > 49:
                        error = "Try a more restricted search. Search limited to the first 50 entries."
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn, title=title, author=author, books=books_ret)
                if bookct <1:
                    error = "No books found with this ISBN and title"
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn, title=title, author=author)
            #ISBN and Author
            if isbnsearch != "%" and titlesearch == "%" and authorsearch != "%":
                books_ret = db.execute("SELECT * FROM books \
                   WHERE books.isbn LIKE :isbnsearch AND books.author LIKE :authorsearch LIMIT 50", \
                   {"isbnsearch": isbnsearch,"authorsearch": authorsearch}).fetchall()
                bookct = 0
                for book in books_ret:
                    bookct += 1
                if bookct>=1:
                    subtitle = "ISBN and Author Search"
                    if bookct > 49:
                        error = "Try a more restricted search. Search limited to the first 50 entries."
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn, title=title, author=author, books=books_ret)
                if bookct <1:
                    error = "No books found with this ISBN and Author"
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn, title=title, author=author)
            #ISBN, Title, and Author
            if isbnsearch != "%" and titlesearch != "%" and authorsearch != "%":
                books_ret = db.execute("SELECT * FROM books \
                   WHERE books.isbn LIKE :isbnsearch AND books.title LIKE :titlesearch AND \
                   books.author LIKE :authorsearch LIMIT 50", \
                   {"isbnsearch": isbnsearch, "titlesearch": titlesearch, "authorsearch": authorsearch}).fetchall()
                bookct = 0
                for book in books_ret:
                    bookct += 1
                if bookct>=1:
                    subtitle = "ISBN, Title and Author Search"
                    if bookct > 49:
                        error = "Try a more restricted search. Search limited to the first 50 entries."
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn, title=title, author=author, books=books_ret)
                if bookct <1:
                    error = "No books found with this ISBN, Title and Author"
                    return render_template("books.html", subtitle=subtitle, error=error, isbn=isbn, title=title, author=author)

            else: #Resume Here
                return "Something is wrong"

        except:
            subtitle = "Error in Seach Form"
            i=0
            render_template("books.html", subtitle=subtitle, error=error, isbn=isbn,
            title=title, author=author, books=books_ret, currentisbn=currentisbn, bookct=bookct,i=i)


@app.route("/bookpage",methods=['POST','GET'])
@login_required
def bookpage():
    subtitle="Book page"
    global currentisbn
    user=session['user_id']
    isbn = request.form['bookisbn']
    currentisbn=isbn
    reviews, books, book_reviewed, books_json, revcount = get_reviews()
    nratings = books_json['books']['work_ratings_count']
    avgrating = books_json['books']['average_rating']
    error = book_reviewed
    title=books.title
    author=books.author
    pubyear=books.pubyear
    if request.method == 'POST':
        try:
            return render_template("bookpage.html", subtitle=subtitle, isbn=isbn,
            books=books, nratings=nratings, avgrating=avgrating,
            title=title, author=author, pubyear=pubyear, error=error, book_reviewed=book_reviewed,
            reviews=reviews, user=user, revcount=revcount)
        except:
            error = "Error in bookpage"
            return render_template("search.html", subtitle=subtitle, error=author)
            return render_template("bookpage.html", subtitle=subtitle, error=error, isbn=isbn,
            title=title, author=author, books=books)
    else:
        error = "line 260 error in request.method == 'POST'"
        return render_template("bookpage.html", subtitle=subtitle, error=error, book=book)


def get_reviews():
    global currentisbn
    isbn=currentisbn
    user=session['user_id']
    res = requests.get("https://www.goodreads.com/book/review_counts.json", \
    params={"key": " hj7IlmJs5Em6ojWbiZy8A", "isbns": isbn})
    try:
        #Initialize Data
        books_data = {'work_ratings_count': 0,'average_rating': 0.0}
        books_json ={'books': books_data}
        data_json = res.json()
        #work_ratings_count = -2
        work_ratings_count = data_json['books'][0]['work_ratings_count'] # This works
        average_rating = data_json['books'][0]['average_rating']
        #books_data = {'work_ratings_count': -2,'average_rating': 0.0} # This works
        books_data = {'work_ratings_count': work_ratings_count,'average_rating': average_rating} # This works
        books_json = {'books': books_data}
    except:
        books_data = {'work_ratings_count': -1,'average_rating': 0.0}
        books_json = {'books': books_data}
    books = db.execute("SELECT * FROM books WHERE books.isbn = :isbn", {"isbn": isbn}).fetchone()
    book_reviewed = False
    reviews = db.execute("SELECT user_id, username, num_stars, review, review_id \
        FROM user_rev1 RIGHT JOIN reviews ON reviews.user_id = user_rev1.id \
        WHERE reviews.book_id=:isbn", {"isbn": isbn}).fetchall()
    revcount = 0
    for review in reviews:
        revcount +=1
        if review.user_id == session['user_id']:
                book_reviewed = True
    return reviews, books, book_reviewed, books_json, revcount


@app.route('/submitreview',methods=['POST','GET'])
@login_required
def submitreview():
    subtitle="Your Review"
    global currentisbn
    isbn=currentisbn
    user=session['user_id']
    reviews, books, book_reviewed, books_json, revcount = get_reviews()
    error = book_reviewed
    title=books.title
    author=books.author
    if request.method == 'POST':
        number_stars = -1
        book_id=currentisbn
        user_id=session['user_id']
        review = request.form['reviewtext']
        try:
            num_stars = request.form['options']
        except:
            num_stars = 0
        #Prevent duplicate review on refresh
        if book_reviewed != True:
            db.execute("INSERT INTO reviews (user_id, book_id, num_stars, review) \
            VALUES (:user_id, :book_id, :num_stars, :review)",
            {"user_id": user_id, "book_id": book_id, "num_stars": num_stars, "review": review})
            db.commit()
        reviews, books, book_reviewed, books_json, revcount = get_reviews()
        nratings = books_json['books']['work_ratings_count']
        avgrating = books_json['books']['average_rating']
        title=books.title
        author=books.author
        try:
            return render_template("bookpage.html", subtitle=subtitle, isbn=isbn,
            books=books, nratings=nratings, avgrating=avgrating,
            title=title, author=author, error=error, book_reviewed=book_reviewed,
            reviews=reviews, user=user, revcount=revcount)
        except:
            return "line 442"


@app.route("/delete",methods=['POST','GET'])
@login_required
def delete():
    subtitle="Deleting My Review"
    global currentisbn
    isbn=currentisbn
    user_id=session['user_id']
    review = db.execute("SELECT review_id FROM reviews \
        WHERE reviews.book_id=:isbn AND reviews.user_id=:user_id", \
        {"isbn": isbn, "user_id": user_id}).fetchone()
    review_id=review[0]
    db.execute("DELETE FROM reviews WHERE review_id=:review_id", \
    {"review_id": review_id})
    db.commit()
    subtitle="Deleted Review"
    nratings="add nratings"
    avgrating="avgrating"
    reviews, books, book_reviewed, books_json, revcount = get_reviews()
    error = book_reviewed
    title=books.title
    author=books.author
    book_reviewed = False
    return render_template("bookpage.html", subtitle=subtitle, isbn=isbn,
    books=books, nratings=nratings, avgrating=avgrating,
    title=title, author=author, error=error, book_reviewed=book_reviewed,
    reviews=reviews, user=session['user_id'],revcount=revcount)


@app.route('/edit',methods=['POST','GET'])
@login_required
def edit():
    subtitle="Edit Review"
    #return "line 441"
    global currentisbn
    isbn=currentisbn
    user=session['user_id']
    reviews, books, book_reviewed, books_json, revcount = get_reviews()
    error = book_reviewed
    title=books.title
    author=books.author
    if request.method == 'POST':
        number_stars = -1
        book_id=currentisbn
        user_id=session['user_id']
        for review in reviews:
            current_review = review.review
            num_stars = review.num_stars
        reviews, books, book_reviewed, books_json, revcount = get_reviews()
        nratings = books_json['books']['work_ratings_count']
        avgrating = books_json['books']['average_rating']
        #for book in books
        title=books.title
        author=books.author
        return render_template("edit.html", subtitle=subtitle, isbn=isbn,
        books=books, nratings=nratings, avgrating=avgrating,
        title=title, author=author, error=error, book_reviewed=book_reviewed,
        reviews=reviews, user=user, revcount=revcount)

        try:
            return render_template("edit.html", subtitle=subtitle, isbn=isbn,
            books=books, nratings=nratings, avgrating=avgrating,
            title=title, author=author, error=error, book_reviewed=book_reviewed,
            reviews=reviews, user=user)
        except:
            return "line 486"
        return "line 487"


@app.route('/cancel',methods=['POST','GET'])
@login_required
def cancel():
    subtitle="Review Canceled"
    global currentisbn
    isbn=currentisbn
    user=session['user_id']
    user_id=session['user_id']
    book_id=currentisbn
    reviews, books, book_reviewed, books_json, revcount = get_reviews()
    error = book_reviewed
    #return books.title
    title=books.title
    author=books.author
    nratings = books_json['books']['work_ratings_count']
    avgrating = books_json['books']['average_rating']
    try:
        return render_template("bookpage.html", subtitle=subtitle, isbn=isbn,
        books=books, nratings=nratings, avgrating=avgrating,
        title=title, author=author, error=error, book_reviewed=book_reviewed,
        reviews=reviews, user=user,revcount=revcount)
    except:
        return "line 509"


@app.route('/updatereview',methods=['POST','GET'])
@login_required
def updatereview():
    subtitle="Update Review"
    global currentisbn
    isbn=currentisbn
    user=session['user_id']
    reviews, books, book_reviewed, books_json, revcount = get_reviews()
    error = book_reviewed
    title=books.title
    author=books.author
    #return books.title
    if request.method == 'POST':
        number_stars = -1
        book_id=currentisbn
        user_id=session['user_id']
        newreview = request.form['reviewtext']
        for review in reviews:
            if user_id == review.user_id:
                current_review = review.review
                num_stars = review.num_stars
                review_id=review.review_id
        try:
            num_stars = request.form['options']
        except:
            num_stars = 0
        x = db.execute("UPDATE reviews SET review = :newreview, num_stars = :num_stars \
        WHERE review_id = :id" \
        ,{"newreview": newreview, "id": review_id, "num_stars": num_stars})
        db.commit()
        subtitle="Updated Review"
        error=""
        reviews, books, book_reviewed, books_json, revcount = get_reviews()
        nratings = books_json['books']['work_ratings_count']
        avgrating = books_json['books']['average_rating']
        title=books.title
        author=books.author
        try:
            return render_template("bookpage.html", subtitle=subtitle, isbn=isbn,
            books=books, nratings=nratings, avgrating=avgrating,
            title=title, author=author, error=error, book_reviewed=book_reviewed,
            reviews=reviews, user=user,revcount=revcount)
        except:
            return "line 538"


@app.route("/test",methods=['POST','GET'])
@login_required
def test():
    subtitle="Search for Books"
    error=""
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
