#!/usr/bin/python

from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import TCPServer
import os

port = 80
directory = os.path.join(os.path.dirname(__file__), '/etc/sdn')
os.chdir(directory)
TCPServer.allow_reuse_address = True
httpd = TCPServer(("", port), SimpleHTTPRequestHandler)
print 'Starting HTTP Server on port', port, '...'
httpd.serve_forever()