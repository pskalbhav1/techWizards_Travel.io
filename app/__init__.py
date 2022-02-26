import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

from app import routes

db = SQLAlchemy(app)

if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(debug=True)