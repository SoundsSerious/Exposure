# -*- coding: utf-8 -*-
"""
Created on Sat Oct 22 16:57:29 2016

@author: Cabin
"""
import copy
import sys

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from kivy.graphics import *
from kivy.graphics.vertex_instructions import *
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.properties import (
    ListProperty, NumericProperty, BooleanProperty, ObjectProperty)

from twisted.words.xish import domish
from twisted.internet.task import LoopingCall
from twisted.words.protocols.jabber.jid import JID
from twisted.application import service
from twisted.words.protocols.jabber import jid
from twisted.internet import reactor, protocol

from wokkel.xmppim import MessageProtocol, AvailablePresence,PresenceProtocol
from wokkel.client import XMPPClient
from wokkel.xmppim import RosterClientProtocol

from kivy.lang import Builder

from config import *
from log import *
from style import *

def generateJID( dom, usr=None, res=None):
    if usr: usr += '@'
    if res: res = '\\'+res
    ident =  "{user}{domain}{resource}".format(user = usr,\
                                        domain = dom,\
                                        resource = res)
    print 'MAKING JID: {}'.format(ident)
    return JID(ident)

# Configuration parameters

DOMAIN = 'exposureapp.io'
SECRET = 'secret'
RESOURCE = ''
LOG_TRAFFIC = True
USER = 'echo'
SERVER = 'test'

Builder.load_string('''
<Conversation>:
    #Put These Here To Access Outside KV
    input: input
    messages: messages
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            id: messages
            orientation: 'vertical'
        TextInput:
            id: input
            multiline: False
            size_hint: (1,0.1)

''')

'''
Sample Code::::::

if msg["type"] == 'chat' and hasattr(msg, "body"):
    self._app._log.addText('{:<30}||{}'.format(msg['from'],msg.body))
    reply = domish.Element((None, "message"))
    reply["to"] = msg["from"]
    reply["from"] = msg["to"]
    reply["type"] = 'chat'
    reply.addElement("body", content="echo: Yo!" + str(msg.body))

    self.send(reply)

            lay.add_widget(RoundedLabel(text = 'Hey Hey How Are You?',halign='right',\
                                        background_color = (1,1,1,0.8),\
                                        font_color = (0,0.2,0.5)))
            lay.add_widget(RoundedLabel(text = 'Hey Hey How Are You?',halign='left',\
                                        background_color = (1,1,1,0.8),\
                                        font_color = (0,0.2,0.5)))
'''
class Conversation(ScrollView):
    '''In Which We Store A Conversation'''
    _app = None
    _other_jid = None

    _self_color = (0.78,0.78,0.8)
    _self_font = (0,0,0)

    _other_color = (0.1,0.84,0.99)
    _other_font = (1,1,1,1)

    def __init__(self,app, other_jid):
        super(Conversation,self).__init__()

        self._app = app
        self._other_jid = other_jid

        self.input.bind( on_text_validate = self.sendMessage )

    @property
    def app(self):
        return self._app

    @property
    def other_jid(self):
        return self._other_jid

    def sendMessage(self, instance):
        #
        reply = domish.Element((None, "message"))
        reply["to"] = self.other_jid
        reply["from"] = self.app.self_jid
        reply["type"] = 'chat'
        reply.addElement("body", content= str(instance.text) )

        #Add To Conversation & Send Through Messages App
        self.addMessage(reply)
        self.app.xmpp_client.send(reply)

        instance.text = ''

    def addMessage(self, msg):
        if str(msg.body).strip(): # CHeck For Whitespace
            #Determine From JID, If Same As Self_JID put on right, otherwise move dat ish left
            if msg['from'] == self.app.self_jid:
                self.messages.add_widget(RoundedLabel(text = str(msg.body),\
                                                      halign='right',\
                                                      width_frac = self.width * 0.66,\
                                                      background_color = self._self_color,\
                                                      font_color = self._self_font))
            else:
                self.messages.add_widget(RoundedLabel(text = str(msg.body),\
                                                      halign='left',\
                                                      width_frac = self.width * 0.66,\
                                                      background_color = self._other_color,\
                                                      font_color = self._other_font))


class PeerMessageProtocol(MessageProtocol):

    _message = 'Yo Didddly Do Neighborino!'
    _app = None

    def __init__(self, app_instance):
        super(PeerMessageProtocol, self).__init__()

        self._app = app_instance

        self.target = self._app._other_jid
        self.entity = self._app._self_jid

    @property
    def app(self):
        return self._app

    def connectionMade(self):
        print  "Connected!"

        # send initial presence
        self.send(AvailablePresence())

    def connectionLost(self, reason):
        print  "Disconnected!"

    def onMessage(self, msg):

        #Check If Its A Chat Message
        if msg["type"] == 'chat' and hasattr(msg, "body"):
            #Do Message Stuff (ie.. Add It To The Conversation)
            self.app.conversation.addMessage(msg)

class RosterHandler(RosterClientProtocol):

    _app = None

    def __init__(self,app):
        super(RosterHandler,self).__init__()
        self._app = app

    def gotRoster(self, roster):
        self._roster = roster
        self._app._log.addText( 'Got roster: {}'.format(roster) )
        for entity, item in roster.iteritems():
            self._app._log.addText('  %r (%r)' % (entity, item.name or ''))

    def connectionInitialized(self):
        RosterClientProtocol.connectionInitialized(self)
        d = self.getRoster()
        d.addCallback(self.gotRoster)
        d.addErrback(lambda x: sys.stdout.write )
        
class MessageWidget(Widget):

        _xmppclient = None
        _self_jid = None
        _other_jid = None
        app = None
        def __init__(self,app):
            super(MessageWidget,self).__init__()
            self.app = app
            self._self_jid = generateJID(DOMAIN, USER, RESOURCE)
            self._other_jid = generateJID(DOMAIN, SERVER, RESOURCE)

            self.createXMPPClient()

            self._conversation = Conversation(self, self.other_jid)

            self.startNetworkService()

            self.add_widget(self._conversation)
            
            self.bind(pos=self.update_rect,
                      size = self.update_rect)
        
        def update_rect(self,*args):
            self._conversation.size = self.size            

        @property
        def self_jid(self):
            return self._self_jid.full()

        @property
        def other_jid(self):
            return self._other_jid.full()

        @property
        def xmpp_client(self):
            return self._xmppclient

        @property
        def conversation(self):
            return self._conversation

        def startNetworkService(self):
            self.xmpp_client.startService()

        def createXMPPClient(self):
            self._xmppclient = XMPPClient( self._self_jid, SECRET)
            self.xmpp_client.logTraffic = LOG_TRAFFIC

            echobot = PeerMessageProtocol(self)
            echobot.setHandlerParent(self.xmpp_client)

            self._roster = RosterHandler(self)
            self._roster.setHandlerParent(self.xmpp_client)

            presence = PresenceProtocol()
            presence.setHandlerParent(self.xmpp_client)
            presence.available()

if __name__ == '__main__':

    class MessageApp(App):

        _xmppclient = None
        _self_jid = None
        _other_jid = None

        def build(self):
            self._self_jid = generateJID(DOMAIN, USER, RESOURCE)
            self._other_jid = generateJID(DOMAIN, SERVER, RESOURCE)

            self.createXMPPClient()

            self._conversation = Conversation(self, self.other_jid)

            self.startNetworkService()

            return self._conversation

        @property
        def self_jid(self):
            return self._self_jid.full()

        @property
        def other_jid(self):
            return self._other_jid.full()

        @property
        def xmpp_client(self):
            return self._xmppclient

        @property
        def conversation(self):
            return self._conversation

        def startNetworkService(self):
            self.xmpp_client.startService()

        def createXMPPClient(self):
            self._xmppclient = XMPPClient( self._self_jid, SECRET)
            self.xmpp_client.logTraffic = LOG_TRAFFIC

            echobot = PeerMessageProtocol(self)
            echobot.setHandlerParent(self.xmpp_client)

            self._roster = RosterHandler(self)
            self._roster.setHandlerParent(self.xmpp_client)

            presence = PresenceProtocol()
            presence.setHandlerParent(self.xmpp_client)
            presence.available()


    app = MessageApp()
    app.run()