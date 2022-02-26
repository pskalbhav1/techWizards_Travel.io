import os
from flask import Flask, request, jsonify,render_template,session,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import wraps

#voice
import geocoder
from csv import reader
from translate import Translator
from langdetect import detect
from gtts import gTTS
import folium
import speech_recognition as sr
from playsound import playsound

from dotenv import load_dotenv
load_dotenv()

from flask_socketio import SocketIO,join_room,leave_room

from app import app

app.config['SECRET_KEY']=os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
# socketio = SocketIO(app)

class Users(db.Model):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.Integer)
    email = db.Column(db.String(50))
    name = db.Column(db.String(50))
    password = db.Column(db.String(50))
    admin = db.Column(db.Boolean)
    websocket_id = db.Column(db.String, unique=True, index=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member1 = db.Column(db.Integer)
    member2 = db.Column(db.Integer)

# class Message(db.Model):
#     __tablename__ = 'messages'
#     id = db.Column(db.Integer(), primary_key=True)
#     url = db.Column(db.String())
#     sender_id = db.Column(db.String())
#     recipient_id = db.Column(db.String())
#     body = db.Column(db.String())
#     timestamp = db.Column(db.DateTime)
#     read = db.Column(db.Boolean(), default=False)
#     thread_id = db.Column(db.String())
#     sender_del = db.Column(db.Boolean())
#     recipient_del = db.Column(db.Boolean())

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/")
def index():
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
                session['publicid'] = user.public_id
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

@app.route('/community',methods=['GET','POST'])
def community():
    return render_template('community.html')

@app.route("/room",methods=['GET','POST'])
def room():
    room = None
    if request.method=='POST':
        member1 = session.get('publicid')
        member2 = request.form['member2']

        room = Room.query.filter_by(member1=member1,member2=member2).first()
        if not room:
            room = Room.query.filter_by(member1=member2,member2=member1).first()
        if not room:
            new_room = Room(member1=member1,member2=member2) 
            db.session.add(new_room)  
            db.session.commit() 
            room = Room.query.filter_by(member1=member1,member2=member2).first()
        session['room'] = room.id
        session['member2'] = member2
    return render_template('chat.html',room=room)    


location=''
language=''
text=''
xext=''
def translate(language,text):
    ip = geocoder.ip("me")
    location = ip.latlng
    map = folium.Map(location=location, zoom_start=10)
    folium.CircleMarker(location=location, radius=50, color="red").add_to(map)
    folium.Marker(location).add_to(map)
    map.save("map.html")
    with open('data.csv', 'r') as read_obj:
        csv_reader = reader(read_obj)
        for row in csv_reader:
            if row[0]==ip.city:
                language=row[1]
    r = sr.Recognizer() 
    i=0
    while text!='bye':
        try:
            with sr.Microphone() as source2:
                r.adjust_for_ambient_noise(source2, duration=0.2)
                audio2 = r.listen(source2)
                MyText = r.recognize_google(audio2)
                text = MyText.lower()
                print(text)
                translator= Translator(from_lang=detect(text),to_lang=language)
                translation = translator.translate(text)
                print(translation)
                tts = gTTS(translation)
                tts.save("hi{0}.mp3".format(i))
                playsound("hi{0}.mp3".format(i))
                i=i+1
            with sr.Microphone() as source2:
                r.adjust_for_ambient_noise(source2, duration=0.2)
                audio2 = r.listen(source2)
                MyText = r.recognize_google(audio2)
                xext = MyText.lower()
                print(xext)
                translator= Translator(from_lang=language,to_lang=detect(text))
                translation = translator.translate(xext)
                print(translation)
                tts = gTTS(translation)
                tts.save("hi{0}.mp3".format(i))
                playsound("hi{0}.mp3".format(i))
                i=i+1
              
        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))
          
        except sr.UnknownValueError:
            print("Nothing heard")
        
        except StopIteration:
            return

@app.route("/voice")
def voice():
    # session['stop']=False
    translate(language,text)
    return render_template('index1.html')