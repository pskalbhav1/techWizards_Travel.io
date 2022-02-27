import os
from flask import Flask, request, jsonify,render_template,session,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import wraps
from haversine import inverse_haversine, Direction
from math import pi

#voice
import geocoder
from csv import reader
from translate import Translator
from langdetect import detect
from gtts import gTTS
import folium
import speech_recognition as sr
from playsound import playsound

#places
import osmnx as ox
from geopy.geocoders import Nominatim
import networkx as nx
import haversine as hs
import geopy.distance
import openrouteservice as ors

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
    lat = db.Column(db.String(50))
    long = db.Column(db.String(50))
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
    ip = geocoder.ip("me")
    location = ip.latlng
    print(session['publicid'])
    if session['publicid']:
        user = Users.query.filter_by(public_id=session['publicid']).first()
        user.lat = round(location[0])
        user.long = round(location[1])
        db.session.commit()
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
                session['name']=user.name
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
    ip=geocoder.ip("me")
    loc=ip.latlng
    print(ip)
    map = folium.Map(location=loc, zoom_start=10)
    folium.CircleMarker(location=loc, radius=50, color="blue").add_to(map)
    folium.Marker(loc).add_to(map)
    #finding nearby locations
    loc1=inverse_haversine(loc, 40, Direction.WEST)
    loc2=inverse_haversine(loc, 40, Direction.EAST)
    loc3=inverse_haversine(loc, 40, Direction.SOUTH)
    loc4=inverse_haversine(loc, 40, Direction.NORTH)
    user = Users.query.filter_by(lat=loc1[0],long=loc1[1]).first()
    if user:
        folium.CircleMarker(location=loc1,popup = 'location', radius=50, color="red").add_to(map)
        folium.Marker(loc1).add_to(map)
    user = Users.query.filter_by(lat=loc2[0],long=loc2[1]).first()
    if user:
        folium.CircleMarker(location=loc2,popup = user.public_id, radius=50, color="red").add_to(map)
        folium.Marker(loc2).add_to(map)
    user = Users.query.filter_by(lat=loc3[0],long=loc3[1]).first()
    if user:
        folium.CircleMarker(location=loc3,popup = 'location', radius=50, color="red").add_to(map)
        folium.Marker(loc3).add_to(map)
    user = Users.query.filter_by(lat=loc4[0],long=loc4[1]).first()
    # if user:
    folium.CircleMarker(location=loc4,popup = 'user', radius=50, color="red").add_to(map)
    folium.Marker(loc4).add_to(map)
    return render_template('community.html',map=map._repr_html_())

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
    # map = folium.Map(location=location, zoom_start=10)
    # folium.CircleMarker(location=location, radius=50, color="red").add_to(map)
    # folium.Marker(location).add_to(map)
    # map.save("map.html")
    target = os.path.join(app.static_folder,'data.csv')
    with open(target, 'r') as read_obj:
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

@app.route("/translatevoice")
def translatevoice():
    ip = geocoder.ip("me")
    location = ip.latlng
    map = folium.Map(location=location, zoom_start=10)
    folium.CircleMarker(location=location, radius=50, color="red").add_to(map)
    folium.Marker(location).add_to(map)
    return render_template('translate.html',map=map._repr_html_())

@app.route("/voice")
def voice():
    # session['stop']=False
    translate(language,text)
    return render_template('index1.html')

@app.route('/test')
def test():
    ip = geocoder.ip("me")
    location = ip.latlng
    map = folium.Map(location=location, zoom_start=10)
    folium.CircleMarker(location=location, radius=50, color="red").add_to(map)
    folium.Marker(location).add_to(map)
    return render_template('test.html',map=map._repr_html_())

#places
def getAttraction(m, place, graph, orig_node, dest_node, dist):
    atttag = {'tourism' : 'attraction'}
    att = ox.geometries_from_place(place, tags = atttag)
    att_points = att[att.geom_type == 'Point'][:100]
    attlocs = zip(att_points.geometry.y, att_points.geometry.x)
    attname = att_points.name
    index = 0
    for location in attlocs:
        currloc = ox.get_nearest_node(graph, location)
        if nx.has_path(graph, orig_node, currloc) == False or nx.has_path(graph, currloc, dest_node) == False:
            index += 1
            continue
        dist1 = nx.shortest_path_length(graph, orig_node, currloc)
        dist2 = nx.shortest_path_length(graph, currloc, dest_node)
        d = dist1 + dist2
        if d <= 30 + dist:
            folium.Marker(location = location, icon=folium.Icon(color='blue'), popup = attname[index]).add_to(m)
        index += 1 
    return m
        
def getPub(m, place, graph, orig_node, dest_node, dist):
    pubtag = {'amenity' : 'pub'}
    pub = ox.geometries_from_place(place, tags = pubtag)
    pub_points = pub[pub.geom_type == 'Point'][:100]
    publocs = zip(pub_points.geometry.y, pub_points.geometry.x)
    pubname = pub_points.name
    index = 0
    for location in publocs:
        currloc = ox.get_nearest_node(graph, location)
        if nx.has_path(graph, orig_node, currloc) == False or nx.has_path(graph, currloc, dest_node) == False:
            index += 1
            continue
        dist1 = nx.shortest_path_length(graph, orig_node, currloc)
        dist2 = nx.shortest_path_length(graph, currloc, dest_node)
        d = dist1 + dist2
        if d <= 30 + dist:
            folium.Marker(location = location, icon=folium.Icon(color='orange'), popup = pubname[index]).add_to(m)
        index += 1  
    return m

def getPark(m, place, graph, orig_node, dest_node, dist):
    parktag = {'leisure' : 'park'}
    park = ox.geometries_from_place(place, tags = parktag)
    park_points = park[park.geom_type == 'Point'][:100]
    parklocs = zip(park_points.geometry.y, park_points.geometry.x)
    parkname = park_points.name
    index = 0
    for location in parklocs:
        currloc = ox.get_nearest_node(graph, location)
        if nx.has_path(graph, orig_node, currloc) == False or nx.has_path(graph, currloc, dest_node) == False:
            index += 1
            continue
        dist1 = nx.shortest_path_length(graph, orig_node, currloc)
        dist2 = nx.shortest_path_length(graph, currloc, dest_node)
        d = dist1 + dist2
        if d <= 30 + dist:
            folium.Marker(location = location, icon=folium.Icon(color='green'), popup = parkname[index]).add_to(m)
        index += 1  
    return m

def getRestraunt(m, place, graph, orig_node, dest_node, dist):
    rstntag = {'amenity' : 'restaurant'}
    rstn = ox.geometries_from_place(place, tags = rstntag)
    rstn_points = rstn[rstn.geom_type == 'Point'][:100]
    rstnlocs = zip(rstn_points.geometry.y, rstn_points.geometry.x)
    rstnname = rstn_points.name
    index = 0
    for location in rstnlocs:
        currloc = ox.get_nearest_node(graph, location)
        if nx.has_path(graph, orig_node, currloc) == False or nx.has_path(graph, currloc, dest_node) == False:
            index += 1
            continue
        dist1 = nx.shortest_path_length(graph, orig_node, currloc)
        dist2 = nx.shortest_path_length(graph, currloc, dest_node)
        d = dist1 + dist2
        if d <= 30 + dist:
            folium.Marker(location = location, icon=folium.Icon(color='black'), popup = rstnname[index]).add_to(m)
        index += 1  
    return m
    
def getCafe(m, place, graph, orig_node, dest_node, dist):
    cafetag = {'amenity' : 'cafe'}
    cafe = ox.geometries_from_place(place, tags = cafetag)
    cafe_points = cafe[cafe.geom_type == 'Point'][:100]
    cafelocs = zip(cafe_points.geometry.y, cafe_points.geometry.x)
    cafename = cafe_points.name
    index = 0
    for location in cafelocs:
        currloc = ox.get_nearest_node(graph, location)
        if nx.has_path(graph, orig_node, currloc) == False or nx.has_path(graph, currloc, dest_node) == False:
            index += 1
            continue
        dist1 = nx.shortest_path_length(graph, orig_node, currloc)
        dist2 = nx.shortest_path_length(graph, currloc, dest_node)
        d = dist1 + dist2
        if d <= 30 + dist:
            folium.Marker(location = location, icon=folium.Icon(color='orange'), popup = cafename[index]).add_to(m)
        index += 1  
    return m
        
def getHotel(m, place, graph, orig_node, dest_node, dist):
    hoteltag = {'tourism' : 'hotel'}
    hotel = ox.geometries_from_place(place, tags = hoteltag)
    hotel_points = hotel[hotel.geom_type == 'Point'][:100]
    hotellocs = zip(hotel_points.geometry.y, hotel_points.geometry.x)
    hotelname = hotel_points.name
    index = 0
    for location in hotellocs:
        currloc = ox.get_nearest_node(graph, location)
        if nx.has_path(graph, orig_node, currloc) == False or nx.has_path(graph, currloc, dest_node) == False:
            index += 1
            continue
        dist1 = nx.shortest_path_length(graph, orig_node, currloc)
        dist2 = nx.shortest_path_length(graph, currloc, dest_node)
        d = dist1 + dist2
        if d <= 30 + dist:
            folium.Marker(location = location, icon=folium.Icon(color='red'), popup = hotelname[index]).add_to(m)
        index += 1  
    return m
        

def initialMap(place, final_dest, att_flag, park_flag, hotel_flag, rstn_flag, cafe_flag, pub_flag):
    loc = Nominatim(user_agent = 'GetLoc')
    getLoc = loc.geocode(place)

    tloc = Nominatim(user_agent = 'GetLoc') 
    getFLoc = tloc.geocode(final_dest)

    loc1 = (getLoc.latitude, getLoc.longitude)
    loc2 = (getFLoc.latitude, getFLoc.longitude)

    graph = ox.graph_from_place(place, network_type = "drive")
    orig_node = ox.get_nearest_node(graph, loc1)
    dest_node = ox.get_nearest_node(graph, loc2)
    
    shortest_route = nx.shortest_path(graph, orig_node, dest_node, weight = "distance")
    m = ox.plot_route_folium(graph, shortest_route)
    dist = nx.shortest_path_length(graph, orig_node, dest_node)
    
    start = folium.Marker(location = loc1, popup = place, icon = folium.Icon(color='purple')).add_to(m)
    end = folium.Marker(location = loc2,  popup = final_dest, icon = folium.Icon(color='purple')).add_to(m)

    if att_flag == True:
        m = getAttraction(m,place,graph, orig_node, dest_node, dist)
    if park_flag == True:
        m = getPark(m,place,graph, orig_node, dest_node, dist)
    if hotel_flag == True:
        m = getHotel(m,place,graph, orig_node, dest_node, dist)
    if rstn_flag == True:
        m = getRestraunt(m,place,graph, orig_node, dest_node, dist)
    if cafe_flag == True:
        m = getCafe(m,place,graph, orig_node, dest_node, dist)
    if pub_flag == True:
        m = getPub(m,place,graph, orig_node, dest_node, dist)
        
    # m.save("route.html")
    return m


@app.route('/places')
def places():
    # m = initialMap('Bangalore', 'Mysuru', True, False, False, False, False, False)
    return render_template('places.html')