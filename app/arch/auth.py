# -*- coding: utf-8 -*-
"""
Created on Sun Nov 06 19:19:31 2016

@author: Sup
"""

#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from zope.interface import implements, implementer, Interface

from twisted.internet import reactor
from twisted.protocols import basic
from twisted.cred import credentials
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

from sys import stdout

class IEmailStorage(credentials.ICredentials):
    '''Check If Email Has Been Registered, If Not Register'''
    
    def checkEmails(email):
        '''where we check if emails are in EMAILS'''

@implementer(IEmailStorage)
class EmailAuth(object):

    def __init__(self, email):
        self.email = email

class Social_Client(basic.LineReceiver):
    
    def __init__(self, email):
        self.email = email
    
    def connectionMade(self):
        self.sendLine( 'AUTH: {}'.format(self.email) )
    
    def lineReceived(self,line):
        print line

class EchoClientFactory(ReconnectingClientFactory):
    
    _email = None    
    
    def __init__(self, auth_email):
        self.email = auth_email
    
    def startedConnecting(self, connector):
        print 'started connecitng'
        
    def buildProtocol(self, addr):
        print 'building {}'.format(addr)
        self.resetDelay()
        return Social_Client(self.email)

    def clientConnectionLost(self, connector, reason):
        print 'lost connection',reason
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print 'failed connection',reason
        ReconnectingClientFactory.clientConnectionFailed(self, connector,reason)
        

if __name__ == '__main__':
    
    reactor.connectTCP(host, port, EchoClientFactory(email))
    reactor.run()