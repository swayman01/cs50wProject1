import os
import functools

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
#engine = create_engine('postgres://swuklgswqdvenp:3362f809de63cc65ad1f87c891fe7ab68da19a6738f01a3e80e866c0f799a8cf@ec2-50-16-196-57.compute-1.amazonaws.com:5432/dcevpu14st78ms')

# Check for environment variable
#export DATABASE_URL=postgres://swuklgswqdvenp:3362f809de63cc65ad1f87c891fe7ab68da19a6738f01a3e80e866c0f799a8cf@ec2-50-16-196-57.compute-1.amazonaws.com:5432/dcevpu14st78ms
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
import csv
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
# TODO create table from code
tname='books' #Note that this doesn't work, name is hardcded, change in file (2 places)
try:
#TODO: make tablename a variable
    tables = db.execute("SELECT id FROM books").fetchone()
    table_exists = True
except:
    table_exists = False
if table_exists:
    print( f"{tname} already exists. Do you want to add more \
data (y/n)?")
    ans=input()
    if ans == "y" or ans == "Y":
        ans=ans
        #skipping to adding new execute_lines
    else:
        exit()
else:
    print("table", tname, "does not exist")
    exit()

with open('books.csv', newline='') as csvfile:
    print ("Adding lines")
    books = csv.reader(csvfile, delimiter=',', quotechar='"')
    nrow = 0
    for row in books:
        isbn=row[0]
        title = row[1]
        author = row[2]
        pubyear = row[3]
        if nrow > 0: #skip header line
            db.execute("INSERT INTO books (isbn, title, author, pubyear) \
            VALUES (:isbn, :title, :author, :pubyear)",
                             {"isbn": isbn, "title": title, "author": author, \
                             "pubyear": pubyear})
        nrow += 1
        # print (isbn)
        # print (title)
        # print (author)
        # print (pubyear)
        # print ("*** New Book ***")
        # print(', '.join(row))
        # categorize each element in the row
        # insert into table
    db.commit()
    print ("Added", nrow, "lines")

# CREATE TABLE books (
#              id SERIAL PRIMARY KEY,
#              isbn VARCHAR,
#              author VARCHAR,
#              title VARCHAR,
#              pubyear VARCHAR
# );
