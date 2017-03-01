# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 19:03:09 2016

@author: Cabin
"""

#from kivy.support import install_twisted_reactor
#install_twisted_reactor()

from zope.interface import implements, implementer, Interface

from twisted.internet import reactor,task, protocol, defer
from twisted.protocols import basic
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.spread import pb
from twisted.spread.pb import PBClientFactory
from twisted.python import log
from twisted.cred.credentials import IAnonymous

from datetime import datetime
import json

from kivy.app import *
from kivy.uix.screenmanager import *
from kivy.properties import *


from config import *
from interfaces import *

@implementer(IEmailStorage)
class EmailAuth(object):

    def __init__(self, email):
        self.email = email


class NetworkData:
    '''Interface To Handle Getting Data From A Server'''
    primary_key = NumericProperty(None)

    def on_primary_key(self,inst,val):
        '''Here we get data from the server'''
        self.initialize()        
    
    def initialize(self,*args):
        '''We setup the kivy object here'''
        pass
    
class EditableNetworkData(NetworkData):
    '''Interface to Receive and Edit Data From A Server'''
    
    def updateServerData(self):
        '''Map Internal Kivy Form Data To Server RPC Method'''
        pass     

class SocialApp(App):

    host = StringProperty(HOME_URL)
    port = StringProperty(SOCIAL_PORT)

    authenticated = BooleanProperty(False)
    social_client = ObjectProperty(None)

    user_id = NumericProperty(None)
    user_object = ObjectProperty(None)

    def build(self):
        print 'Attempting Connection'
        self.connectToServer()
        sm = self.setupMainScreen()
        return sm

    def auth_handler(self, *args):
        pass

    def setupMainScreen(self):
        pass
    
    def update_client(self,value, deffered):
        pass    

    def on_connect(self, client):
        print "connected successfully!"
        self.social_client = client

    def on_social_client(self,instance, value):
        print 'updating social client'
        reactor.callLater(1,self.startUpdate)
        
    def startUpdate(self):
        d = defer.maybeDeferred(self.get_user_id)
        self.update_client( deffered = d )

    def connectToServer(self):
        reactor.connectTCP(self.host, self.port, Social_ClientFactory(self))

    def get_user_id(self):
        if self.social_client and self.authenticated:
            d = self.social_client.perspective.callRemote('user_id')
            return d.addCallback( self._cb_assignUserId )
        else:
            return None

    def _cb_jsonToDict(self, json_information):
        if json_information:
            return json.loads(json_information)
        
            
    def _cb_assignUserId(self,userId):
        print 'assigning user id {}'.format(userId)
        if userId or userId == 0:
            self.user_id = userId
            return userId   

class ReconnectingPBClientFactory(PBClientFactory,
                                 protocol.ReconnectingClientFactory):
    """Reconnecting client factory for PB brokers.

    Like PBClientFactory, but if the connection fails or is lost, the factory
    will attempt to reconnect.

    Right now we use this as the interface to the server on the client side so we only
    provion for one server connection. This would be a problem if we have multiple hubs,
    or adopt a mesh style network (which would be awesome).
    """
    _root = None
    _perspective = None

    def __init__(self):
       PBClientFactory.__init__(self)
       self._doingLogin = False
       self._doingGetPerspective = False
       self.initialize()

    @property
    def root(self):
        return self._root

    @property
    def perspective(self):
        return self._perspective

    def initialize(self,interval=60):
        self.ping()
        l = task.LoopingCall(self.ping)
        l.start(interval) # call every second

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed'
        PBClientFactory.clientConnectionFailed(self, connector, reason)
        # Twisted-1.3 erroneously abandons the connection on non-UserErrors.
        # To avoid this bug, don't upcall, and implement the correct version
        # of the method here.
        if self.continueTrying:
           print 'retrying...'
           self.connector = connector
           self.retry()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost'
        PBClientFactory.clientConnectionLost(self, connector, reason, reconnecting=True)
        RCF = protocol.ReconnectingClientFactory
        RCF.clientConnectionLost(self, connector, reason)
        self._root = None

    def clientConnectionMade(self, broker):
        print 'connection made'
        self.resetDelay()
        PBClientFactory.clientConnectionMade(self, broker)

    def log(self,*args):
        print 'Got {}||\t{}'.format(datetime.now().isoformat(),'|'.join(args))

    def ping(self):
        print 'ping'
        if self.perspective:
            d = self.perspective.callRemote('ping')
            d.addCallback(self.log)

    # newcred methods
    def login(self, credentials, client=None):
        """
        Login and get perspective from remote PB server.

        Currently the following credentials are supported::

        L{twisted.cred.credentials.IUsernamePassword}
        L{twisted.cred.credentials.IAnonymous}

        @rtype: L{Deferred}
        @return: A L{Deferred} which will be called back with a
        L{RemoteReference} for the avatar logged in to, or which will
        errback if login fails.
        """
        d = self.getRootObject()

        if IAnonymous.providedBy(credentials):
            d.addCallback(self._cbLoginAnonymous, client)
        elif IEmailStorage.providedBy(credentials):
            d.addCallback(self._cbEmailLogin, credentials, client)
        else:
            d.addCallback(
                self._cbSendUsername, credentials.username,
                credentials.password, client)
        d.addCallbacks(self._cb_assignPerspective, self._cb_loginFail)
        return d

    def _cbEmailLogin(self, root, credentials, client):
        return root.callRemote("loginEmail", credentials.email, client)

    def _cb_assignPerspective(self, perspective):
        print 'assigning perspective {}'.format(perspective)
        self._perspective = perspective
        return perspective

    def _cb_loginFail(self, why):
        """The login process failed, most likely because of an authorization
        failure (bad password), but it is also possible that we lost the new
        connection before we managed to send our credentials.
        """
        log.msg("ReconnectingPBClientFactory.failedToGetPerspective")
        if why.check(pb.PBConnectionLost):
            log.msg("we lost the brand-new connection")
            # retrying might help here, let clientConnectionLost decide
            return
        # probably authorization
        self.stopTrying() # logging in harder won't help
        log.err(why)
        raise why


class Social_ClientFactory(ReconnectingPBClientFactory):

    app = None

    def __init__(self, app):
        ReconnectingPBClientFactory.__init__(self)
        self.app = app

    def clientConnectionMade(self, broker):
        ReconnectingPBClientFactory.clientConnectionMade(self,broker)
        self.app.on_connect(self)

    def attemptEmailRegistration(self,email):
        d = self.login( EmailAuth(email) )
        return d


#    def failedToGetPerspective(self, why):
#        """The login process failed, most likely because of an authorization
#        failure (bad password), but it is also possible that we lost the new
#        connection before we managed to send our credentials.
#        """
#        log.msg("ReconnectingPBClientFactory.failedToGetPerspective")
#        if why.check(pb.PBConnectionLost):
#            log.msg("we lost the brand-new connection")
#            # retrying might help here, let clientConnectionLost decide
#            return
#        # probably authorization
#        self.stopTrying() # logging in harder won't help
#        log.err(why)

#        if self._doingLogin:
#            print 'doing login'
#            self.doLogin(self._root)
#        if self._doingGetPerspective:
#           self.doGetPerspective(self._root)
#           self.gotRootObject(self._root)
#
##    # oldcred methods
##    def startGettingPerspective(self, username, password, serviceName, perspectiveName=None, client=None):
##        self._doingGetPerspective = True
##        if perspectiveName == None:
##            perspectiveName = username
##            self._oldcredArgs = (username, password, serviceName, perspectiveName, client)
##
##    def doGetPerspective(self, root):
##        #oldcred getPerspective()
##        (username, password, serviceName, perspectiveName, client) = self._oldcredArgs
##        d = self._cbAuthIdentity(root, username, password)
##        d.addCallback(self._cbGetPerspective,
##                       serviceName, perspectiveName, client)
##        d.addErrback(self.log)
##        d.addCallbacks(self.gotPerspective, self.failedToGetPerspective)


