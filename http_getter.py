#!/usr/bin/python

import requests
import threading
import json

def http_get():
	threading.Timer(5.0, http_get).start()
	response = requests.get('http://10.0.0.100:80/data.file')
	with open('/etc/sdn/data.json', 'w') as f:
	    json.dump(response.content, f)
	
http_get()