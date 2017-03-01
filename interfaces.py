# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 20:25:58 2016

@author: Cabin
"""
from zope.interface import Interface
from twisted.cred import credentials

class ISocial(Interface):
    '''Zope Interface Defining Social Interfaces

    Provides Interface For Getting User Information Like Friends & Projects'''

    def get_user_object(self):
        '''Get Information Relating to self'''
        return

    def get_friends(self):
        '''Return Friend Objects Associated With The User'''
        pass

    def get_projects(self):
        '''Return Projects Objects Associated With The User'''
        pass

    def get_local_users(self):
        '''Get Local Users Via GEO information'''
        pass

    def logout(self):
        '''Logs The User Out'''
        pass

    def update(self):
        '''Updates User Interface Attributes (...From Database)'''
        pass


class IEmailStorage(credentials.ICredentials):
    '''Check If Email Has Been Registered, If Not Register'''

    def checkEmails(email):
        '''where we check if emails are in EMAILS'''