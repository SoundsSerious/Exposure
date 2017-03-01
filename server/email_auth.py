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
    credentialInterfaces = [IEmailStorage]

    ids = {}
    
    @ITwistedData.sqlalchemy_method
    def checkEmails(self,session, email):
        '''where we check if emails are in EMAILS'''
        isthere = session.query(exists().where(User.email==email)).first()
        print isthere
        if any(isthere):
            self.getUserId(session,email)
            defer.returnValue(True)
        else:
            defer.returnValue(False)

    @ITwistedData.sqlalchemy_method
    def createUser(self,session, email):
        newUser = User(email = email)
        session.add(newUser)
        session.flush()
        print 'Adding User {}'.format(email)
        self.ids[email] = newUser.id
        return newUser.id
    
    def getUserId(self,session,email):
        user = session.query(User).filter(User.email == email).first()
        print 'got selfuser {}'.format(user)
        if user:
            self.ids[email] = user.id


    def requestAvatarId(self, credentials, firstTry = True, id = None):
        print 'requesting avatarid with {}'.format( credentials )
        d = defer.maybeDeferred(self.checkEmails,credentials.email)

        def _cb_checkOrRegister(foundUser):
            if foundUser: #Check Email List
                    #d.addCallback(lambda arg: self.getUserId(email = credentials.email))
                    return defer.succeed((credentials.email,self.ids[credentials.email]))
            elif validate_email(credentials.email) and firstTry: #Register Email If Valid Address
                #Create New User
                d.addCallback(lambda arg: self.createUser(credentials.email))
                #Recursive Loopback
                d.addCallback(lambda x: self.requestAvatarId(credentials, False, id = x))
            else:
                return defer.fail(credError.UnhandledCredentials())

        def _cb_dbError(failure):
            failure.trap(Exception)
            raise Exception('Got An Error: {}'.format(str(failure)))

        d.addCallback( _cb_checkOrRegister )
        d.addErrback(  _cb_dbError )

        return d


