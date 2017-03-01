# -*- coding: utf-8 -*-
"""
Created on Sun Oct 30 12:22:08 2016

@author: Sup
"""

#!/usr/bin/env python
import zope

from zope.interface import implements, implementer, Interface
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import defer, reactor, protocol
from twisted.protocols import basic

from twisted.cred.portal import IRealm

from validate_email import validate_email

EMAILS = ['keavin7@yahoo.com']

class IEmailStorage(credentials.ICredentials):
    '''Check If Email Has Been Registered, If Not Register'''

    def checkEmails(email):
        '''where we check if emails are in EMAILS'''

@implementer(IEmailStorage)
class EmailAuth(object):

    def __init__(self, email):
        self.email = email

    def checkEmails(self, email):
        '''where we check if emails are in EMAILS'''
        return email in EMAILS

@implementer(checkers.ICredentialsChecker)
class EmailChecker(object):
    credentialInterfaces = [IEmailStorage]

    def __init__(self, emails):
        "passwords: a dict-like object mapping usernames to passwords"
        self.emails = emails

    def requestAvatarId(self, credentials):
        email = credentials.email
        print email,validate_email(email)
        if email in self.emails: #Check Email List
                return defer.succeed(email)
        elif validate_email(email.strip()): #Register Email If Valid Address
            #Create New User
            #...I mean Later

            #Add Email To Emails
            print 'Adding Email: {}'.format(email)
            self.emails.append( email )

            #Recursive Loopback
            return self.requestAvatarId( credentials )
        else:
            return defer.fail(credError.UnhandledCredentials())

class Social_Server(basic.LineReceiver):
    '''In Which We Communicate With The User'''

    _authenticated = False
    portal = None

    def __init__(self, portal):
        self.portal = portal

    def connectionMade(self):
        self.sendLine('Welcome To Email Auth')

    def authenticate(self, email):
        d = defer.maybeDeferred(self.registerEmail, email)
        d.addCallback(self._cbAuth, email)
        d.addErrback(self._cbAuthFail)
        return d

    def _cbAuth(self, ial, error):
        interface, avatar, logout = ial
        self.sendLine('AUTH:SUCCESS, {}'.format(avatar.avatarId))
        self._authenticated = True

    def _cbAuthFail(self, error):
        r = error.trap(credError.UnhandledCredentials)
        if r == credError.UnhandledCredentials:
            self.sendLine('AUTH:BAD_EMAIL')

    def registerEmail(self, email):
        if self.portal is not None:
            return self.portal.login(EmailAuth(email),None,IEmailStorage)
        raise credError.UnauthorizedLogin()

    def echo(self,line):
        print line
        self.sendLine('AUTH\'d:'+line)

    def lineReceived(self, line):
        print line
        if self._authenticated:
            #Check Other Protocols
            self.echo(line)
        else: #Wait For Auth Attempt
            if line.startswith('AUTH:'):
                email = line.replace('AUTH:','').strip()
                print 'Got Email: {}'.format(email)
                self.authenticate( email )

class ISocial(Interface):

    _user = None
    _projects = None
    _friends = None


    def get_friends(self):
        '''Return A List Of Friend Objects'''
        pass

    def get_projects(self):
        '''Return A List Of Project Objects'''
        pass

    def __call__():
        """Produce an IMessage provider"""




@implementer(ISocial)
class Social_Interface(object):

    def __init__(self,userId):
        self.user = userId

    def perspective_echo(self, text):
        print 'echoing',text
        return text

    def logout(self):
        print self, "logged out"

    def get_friends(self):
        '''Query Database To Get List Of Friend PK's'''

    def get_projects(self):
        '''Query Database To Get List Of Project PK's'''



class Social_AppRealm(object):
    implements(IRealm)

    def requestAvatar(self, user, mind, *cred_interfaces):
        if IEmailStorage in cred_interfaces:
            print avatarId
            avatar = Social_Interface(user)
            return IEmailStorage, avatar, avatar.logout
        else:
            raise NotImplementedError("no interface")

class Social_Factory(protocol.Factory):
    protocol = Social_Server

    def __init__(self, portal):
        self.portal = portal

    def buildProtocol(self, addr):
        p = self.protocol(self.portal)
        p.factory = self
        return p

if __name__ == "__main__":
    print 'Running'
    realm = Social_AppRealm()

    checker = EmailChecker(EMAILS)
    p = portal.Portal(realm, [checker])

    reactor.listenTCP(17776, Social_Factory(p) )
    reactor.run()