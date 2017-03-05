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
            self.createUser(session,email)
            #self.getUserId(session,email)
            defer.returnValue(True)

    def createUser(self,session, email):
        newUser = User(email = email)
        session.add(newUser)
        session.commit() #Moi Moi Importanto! The UID Return Won't Work Otherwise
        print 'Adding User {}'.format(email)
        self.ids[email] = newUser.id
        return newUser.id

    def getUserId(self,session,email):
        user = session.query(User).filter(User.email == email).first()
        print 'got selfuser {}'.format(user)
        if user:
            self.ids[email] = user.id


    def requestAvatarId(self, credentials, firstTry = True, id = None):
        def _cb_dbError(failure):
            failure.trap(Exception)
            raise Exception('Got An Error: {}'.format(str(failure)))

        print 'requesting avatarid with {}'.format( credentials )
        d = defer.maybeDeferred(self.checkEmails,credentials.email)
        d.addErrback(  _cb_dbError )

        def _cb_checkOrRegister(foundUser):
            if foundUser: #Check Email List
                    return defer.succeed((credentials.email,self.ids[credentials.email]))
            else:
                return defer.fail(credError.UnhandledCredentials())

        d.addCallback( _cb_checkOrRegister )
        d.addErrback(  _cb_dbError )

        return d


