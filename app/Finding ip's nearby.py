#!/usr/bin/env python
# coding: utf-8

# In[1]:


import geocoder
import folium
import math
from flask import Flask, request, redirect, url_for, render_template, send_from_directory,Response


# In[2]:


def haversine(lat1, lon1, lat2, lon2):
    # distance between latitudes
    # and longitudes
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0
 
    # convert to radians
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0
 
    # apply formulae
    a = (pow(math.sin(dLat / 2), 2) + pow(math.sin(dLon / 2), 2) * math.cos(lat1) * math.cos(lat2));
    rad = 6371
    c = 2 * math.asin(math.sqrt(a))
    return rad * c


# In[3]:


ips=["192.1.3.8","172.168.1.1","49.15.255.255","49.47.255.255","49.47.25.255"]


# In[4]:


ip=geocoder.ip("me")
loc=ip.latlng
map = folium.Map(location=loc, zoom_start=10)
folium.CircleMarker(location=loc, radius=50, color="blue").add_to(map)
folium.Marker(loc).add_to(map)
map.save("community.html")#The one in blue is you


# In[5]:


def find_ips_closeby():
    for i in ips:
        ip1=geocoder.ip(i)
        loc1=ip1.latlng
        dist=haversine(loc[0],loc[1],loc1[0],loc1[1])
        if dist<5000:
            folium.CircleMarker(location=loc1,popup = 'Location', radius=50, color="red").add_to(map)
            folium.Marker(loc1).add_to(map)
            map.save("community.html")


# In[6]:


find_ips_closeby()

