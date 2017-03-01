# -*- coding: utf-8 -*-
"""
Created on Sat Sep 17 15:59:23 2016

@author: Cabin
"""
#Add Parent Directory For Common Server / App Interface
import sys
sys.path.append('../')

import os,sys
import cyclone.web
from twisted.application import internet
from twisted.application import service

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)


from config import *
from model import *
from social_interface import Social_Component


class MainHandler(cyclone.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

webapp = cyclone.web.Application([
    (r"/", MainHandler),
    (r"/(.*)", cyclone.web.StaticFileHandler,{'path': USR_IMG} )
])

application = service.Application("social server")
top_service = service.MultiService()

#Web Interface
server = internet.TCPServer(WEB_PORT, webapp, interface=HOME_URL)
server.setServiceParent(top_service)

#Social Server
social_server = internet.TCPServer(SOCIAL_PORT, Social_Component(), interface=HOME_URL)
social_server.setServiceParent(top_service)

#Finalize
top_service.setServiceParent(application)