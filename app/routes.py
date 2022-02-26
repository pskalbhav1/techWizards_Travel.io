import os
from flask import Flask, request, jsonify,render_template,session,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import wraps
from dotenv import load_dotenv
load_dotenv()

from app import app

app.config['SECRET_KEY']=os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.Integer)
    email = db.Column(db.String(50))
    name = db.Column(db.String(50))
    password = db.Column(db.String(50))
    admin = db.Column(db.Boolean)


@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/")
def hello():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg=''
    if request.method=='POST':  
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        print(email)

        user = Users.query.filter_by(email=email).first()
        print(user)

        if not email:
            msg = 'Please enter your email'
        elif not name:
            msg = 'Please enter your name'
        elif not password:
            msg = 'Please enter your password'
        elif user:
            msg = 'Account already exists'
        else:
            hashed_password = generate_password_hash(password, method='sha256')
    
            new_user = Users(public_id=str(uuid.uuid4()),email=email, name=name, password=hashed_password, admin=False) 
            db.session.add(new_user)  
            db.session.commit()  
            msg = 'Registered Successfully'

    return render_template('register.html', msg = msg)

@app.route('/login', methods=['GET', 'POST'])  
def login(): 
    msg=''
    if request.method=='POST':  
        email = request.form['email']
        password = request.form['password']
        print(password)  

        user = Users.query.filter_by(email=email).first()

        if not email:
            msg = 'Please enter your email'
        elif not password:
            msg = 'Please enter your password'
        elif not user:
            msg = 'User does not exist'
        else:
            if check_password_hash(user.password,password):
                token = jwt.encode({'public_id': user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])  
                session['loggedin']=True
                session['token']=token
                msg = 'Logged in Successfully'
            else:
                msg = 'Wrong password'

    return render_template('login.html',msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('token', None)
    return redirect(url_for('login'))

@app.route('/users', methods=['GET'])
def get_all_users():  
   
   users = Users.query.all() 

   result = []   

   for user in users:   
       user_data = {}   
       user_data['public_id'] = user.public_id  
       user_data['email'] = user.email
       user_data['name'] = user.name 
       user_data['password'] = user.password
       user_data['admin'] = user.admin 
       
       result.append(user_data)   

   return jsonify({'users': result})