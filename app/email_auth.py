# -*- coding: utf-8 -*-
"""
Created on Sun Dec  4 17:45:56 2016

@author: Cabin
"""
from zope.interface import implements, implementer, Interface
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import defer, reactor, protocol
from twisted.protocols import basic

from sqlalchemy import exists

from twisted.cred.portal import IRealm
from model import *
from validate_email import validate_email

class IEmailStorage(credentials.ICredentials):
    '''Check If Email Has Been Registered, If Not Register'''

    def checkEmails(email):
        '''where we check if emails are in EMAILS'''

@implementer(IEmailStorage)
class EmailAuth(object):

    def __init__(self, email):
        self.email = email.strip()

@implementer(checkers.ICredentialsChecker)
class EmailChecker(object):
    credentialInterfaces = (IEmailStorage,)

    @ITwistedData.sqlalchemy_method
    def checkEmails(self,session, email):
        '''where we check if emails are in EMAILS'''
        isthere = session.query(exists().where(User.email==email)).first()
        if any(isthere):
            defer.returnValue(True)
        else:
            defer.returnValue(False)
    
    @ITwistedData.sqlalchemy_method
    def createUser(self,session, email):
        print session, email
        print 'Adding User {}'.format(email)
        newUser = User(email = email)
        session.add(newUser)


    def requestAvatarId(self, credentials, firstTry = True):
        print 'request avatarid with {}'.format( credentials )
        d = defer.maybeDeferred(self.checkEmails,credentials.email)
        def checkOrRegister(foundUser):
            if foundUser: #Check Email List
                    return defer.succeed(credentials.email)
            elif validate_email(credentials.email) and firstTry: #Register Email If Valid Address
                #Create New User
                d.addCallback(lambda arg: self.createUser(credentials.email))
                #Recursive Loopback
                d.addCallback(lambda arg: self.requestAvatarId(credentials, False))
            else:
                return defer.fail(credError.UnhandledCredentials())
        
        return d.addCallback( checkOrRegister )
        

