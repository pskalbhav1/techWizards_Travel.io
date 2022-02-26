import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

from flask_socketio import SocketIO


db = SQLAlchemy(app)
socketio = SocketIO(app)

from app import routes,events

if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    socketio.run(app,debug=True)