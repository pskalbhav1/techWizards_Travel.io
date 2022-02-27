#!/usr/bin/env python
# coding: utf-8

# In[1]:


import geocoder
import folium
import math
from flask import Flask, request, redirect, url_for, render_template, send_from_directory,Response
from haversine import inverse_haversine, Direction
from math import pi


# In[3]:


ip=geocoder.ip("me")
loc=ip.latlng
map = folium.Map(location=loc, zoom_start=10)
folium.CircleMarker(location=loc, radius=50, color="blue").add_to(map)
folium.Marker(loc).add_to(map)
map.save("community.html")


# In[7]:


def find_ips_closeby():
    loc1=inverse_haversine(loc, 5, Direction.WEST)
    loc2=inverse_haversine(loc, 5, Direction.EAST)
    loc3=inverse_haversine(loc, 5, Direction.SOUTH)
    loc4=inverse_haversine(loc, 5, Direction.NORTH)
    folium.CircleMarker(location=loc1,popup = 'Location', radius=50, color="red").add_to(map)
    folium.Marker(loc1).add_to(map)
    folium.CircleMarker(location=loc2,popup = 'Location', radius=50, color="red").add_to(map)
    folium.Marker(loc2).add_to(map)
    folium.CircleMarker(location=loc3,popup = 'Location', radius=50, color="red").add_to(map)
    folium.Marker(loc3).add_to(map)
    folium.CircleMarker(location=loc4,popup = 'Location', radius=50, color="red").add_to(map)
    folium.Marker(loc4).add_to(map)
    map.save("community.html")


# In[8]:


find_ips_closeby()


# In[ ]:




