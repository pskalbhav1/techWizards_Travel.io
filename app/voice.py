import geocoder
from csv import reader
from translate import Translator
from langdetect import detect
from gtts import gTTS
import folium
import speech_recognition as sr
from playsound import playsound


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