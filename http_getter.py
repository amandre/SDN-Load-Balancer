#!/usr/bin/python

import requests
import threading

def http_get():
	threading.Timer(5.0, http_get).start()
	r = requests.get('http://192.168.99.3:80/data.file')
	r.json()
	
http_get()
