# -*- coding: utf-8 -*-
"""
Created on Sat Nov  5 16:22:10 2016

@author: Cabin
"""

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import AsyncImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FallOutTransition, \
                                    FadeTransition, RiseInTransition

from kivy.properties import *
from kivy.clock import Clock
from kivy.app import App

from config import *
from style import *
from maps import *
from social_interface import *

SAMPLE_IMAGE = 'https://s-media-cache-ak0.pinimg.com/originals/ec/8e/8f/ec8e8f26ee298a6c852a7b7de37bd96b.jpg'
LOCAL_IMAGE = os.path.join(EXP_PATH,'app','Login_Image.jpg')

       


class Login(Widget):

    _background_url = None

    def __init__(self,app, background_url = None):
        self.app = app
        super(Login,self).__init__()
        '''Get Background URL Image, Create Layout, and add login stuff'''
        self._background_url = background_url

        self._lay = FloatLayout(size_hint = (1, 1))
        self._title = Label( text = 'EXPOSURE', \
                            color = PRIMARY_COLOR,
                            font_name= HEADER_FONT,
                            valign = 'bottom', size_hint = (1,0.15),
                            pos_hint = {'center_x':0.5,'center_y':0.9},
                            font_size=80, bold=True)

        self._login = AlignedTextInput(multiline = False,
                                background_color = OFFWHITE,
                                foreground_color = SECONDARY_COLOR,
                                cursor_color = OFFWHITE,
                                font_name = MENU_FONT,
                                hint_text = 'Enter Your Email',
                                hint_text_color = SECONDARY_COLOR,
                                halign = 'center', valign = 'middle',
                                pos_hint = {'center_x':0.5,'center_y':0.5},
                                size_hint = (0.8, 0.05))
        
        self._image = ExpandingImage( source = self._background_url , \
                                      size_hint = (1, 1),
                                      pos_hint = {'center_x':0.5,'center_y':0.5},
                                      keep_ratio = True,
                                      allow_stretch = True,
                                      opacity = 1
                                     )


        self._login.bind( on_text_validate = self.authenticate_login_value)


        self._lay.add_widget(self._image)
        self._lay.add_widget(self._login)
        self._lay.add_widget(self._title)
        self.add_widget(self._lay)

        self.bck_init = False

        self.bind(pos = self.update_rect,
                  size = self.update_rect)
        

    def authenticate_login_value(self,value):
        msg = self._login.text
        if msg and self.app.social_client:
            authAttempt = self.app.social_client.attemptEmailRegistration(str(msg))
            authAttempt.addCallback(self._cb_authSuccess )
            authAttempt.addErrback( self._cb_authFail )
            self._login.text = ""

    def _cb_authSuccess(self,reference):
        print 'Auth Succeeded {}'.format(reference)
        #print dir(reference)
        self.app.authenticated = True
        self.app.connection = reference

    def _cb_authFail(self, reason):
        print 'Auth Succeeded {}'.format(reason)
        self.app.authenticated = False

    def update_rect(self,*args):
        self._lay.size = self.size
        self._lay.pos = self.pos
