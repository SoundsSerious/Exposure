# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 00:18:19 2017

@author: Sup
"""
from kivy.app import App
from kivy.uix.button import *
from kivy.uix.label import *
from kivy.uix.widget import *
from kivy.uix.boxlayout import *
from kivy.uix.floatlayout import *
from kivy.graphics import *
from kivy.graphics.texture import *
from kivy.graphics.vertex_instructions import *
from kivy.uix.behaviors import *
from kivy.uix.image import *
from kivy.uix.effectwidget import *
from kivy.core.text import Label as CoreLabel
from kivy.loader import Loader
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import *
from kivy.uix.textinput import TextInput
from kivy.uix.image import AsyncImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FallOutTransition, \
                                    FadeTransition, RiseInTransition,NoTransition,\
                                    SlideTransition, SwapTransition
from kivy.properties import *
from kivy.clock import Clock
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics.svg import Svg
from kivy.properties import *
from kivy.core.window import Window
from kivy.graphics.opengl import glFinish
from time import time
from kivy.garden.navigationdrawer import NavigationDrawer
from zope.interface import implements, implementer, Interface
from kivy.garden.mapview import MapView
from kivy.garden.smaa import SMAA
from kivy.garden.androidtabs import *


from twisted.internet import reactor
from twisted.protocols import basic
from twisted.cred import credentials
from twisted.internet.protocol import Protocol, ReconnectingClientFactory


from config import *
from style import *
#Window.size = (300, 100)
from maps import *
from projects import *

class SMAAEffect(SMAA):
    def __init__(self,**kwargs):
        super(SMAAEffect,self).__init__( **kwargs )

# -*- coding: utf-8 -*-
from kivy.lang import Builder
Builder.load_string('''
#:import config config
<MenuPanel@BoxLayout>:
    orientation:'vertical'
    background_color: [1,1,1,1]
    size_hint: 1,1
    spacing:20
    canvas:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: self.pos


<-MenuTabSlider@AndroidTabs>:
    carousel: carousel
    tab_bar: tab_bar
    anchor_y: 'bottom'
    tab_bar_height: 30

    tab_indicator_color: config.SECONDARY_COLOR
    text_color_normal: 1,1,1,1
    text_color_active: config.SECONDARY_COLOR
    AndroidTabsMain:
        padding: 0,0,0,tab_bar.height

        AndroidTabsCarousel:
            id: carousel
            anim_move_duration: root.anim_duration
            on_index: root.on_carousel_index(*args)
            on__offset: tab_bar.android_animation(*args)
            on_slides: self.index = root.default_tab
            on_slides: root.on_carousel_index(self, 0)


    AndroidTabsBar:
        id: tab_bar
        carousel: carousel
        scrollview: scrollview
        layout: layout
        size_hint: 1, None
        height: root.tab_bar_height

        AndroidTabsScrollView:
            id: scrollview
            on_width: tab_bar._trigger_update_tab_bar()

            GridLayout:
                id: layout
                rows: 1
                size_hint: None, 1
                width: self.minimum_width
                on_width: tab_bar._trigger_update_tab_bar()
                shadow_frac: 0.05
                canvas.after:
                    Color:
                        rgba: root.tab_indicator_color
                    Rectangle:
                        pos: self.pos
                        size: 0, root.tab_indicator_height
                    Color:
                        rgba: 1,1,1,1
                    Rectangle:
                        source:'resources/vert_trans.png'
                        size: self.width, self.height*self.shadow_frac
                        pos: self.x,self.y+self.height*(1-self.shadow_frac)

<SocialTab@AndroidTabsBase>:
    background_color: 1,1,1,1
    canvas:
        Color:
            rgba: root.background_color
        Rectangle:
            size: self.size
            pos: self.pos
''')

class MenuTabSlider( AndroidTabs ):

    def __init__(self, app, **kwargs):
        super(MenuTabSlider,self).__init__(**kwargs)
        self.app = app

    def addMenuScreenWidget(self,name,new_widget,**kwargs):
        #Add Menu Button
        mt = SocialTab(text = name.capitalize(),widget = new_widget,**kwargs)

        self.add_widget(mt)

class SocialTab( AndroidTabsBase ):
    '''Simple Interface To Wrap Widget In Container

    :text: must be specified as per AndroidTabs Requirement

    :widget: Use this to wrap a widget

    '''

    wig = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(SocialTab,self).__init__(**kwargs)
        #Screens Should Expand...
        self.size_hint = (1,1)
        self.wig = kwargs.get('widget',self.wig)
        self.wig.size_hint = (1,1)

        self.bind(size = self.update_rect)

    def on_wig(self,intance,value):
        self.add_widget(self.wig)
        self.wig.size = self.size

    def update_rect(self,*args):
        self.wig.size = self.size

class MyTab(Image,AndroidTabsBase):
    source = r'icons/award_gold.png'
    pass



class MenuBar(BoxLayout):
    app = ObjectProperty(None)
    initialized = BooleanProperty(False)
    bar_height = NumericProperty(50)

    def __init__(self, app, **kwargs):
        super(MenuBar,self).__init__(**kwargs)
        self.app = app
        self.bar_height = kwargs.get('bar_height',self.bar_height)

        self.setupMenu()
        self.setupAppPanel()

        #Callbacks
        self.bind(pos =  self.update_rect,
                  size = self.update_rect)



    def setupMenu(self):
        self.orientation = 'vertical'
        self.menu = BoxLayout(size_hint=(1,0.075))
        self.menu.orientation = 'horizontal'
        self.menu.height = self.bar_height
        self.add_widget(self.menu)

    def setupAppPanel(self):
        #The Second Added Is For the Main Widget
        self.menuScreenManager = ScreenManager(transition=NoTransition())
        self.add_widget(self.menuScreenManager)

    def addMenuScreenWidget(self,name,new_widget,**kwargs):
        #Add Menu Button
        button= RoundedButton(text=name,**kwargs)
        #with button.canvas:
        button.height = self.bar_height
        self.menu.add_widget(button)
        button.bind( on_press = lambda *args: self.changeScreen(name) )

        #Add The Widget Itself
        screen = Screen(name = name)
        screen.add_widget(new_widget)

        self.menuScreenManager.add_widget(screen)

    def changeScreen(self,screenName):
        self.menuScreenManager.current = screenName

    def update_rect(self,*args):
        print self.menu.size, self.menu.children[0].size

class SocialNavigationBar(NavigationDrawer):
    touch_accept_height = NumericProperty(200)

    def on_touch_down(self, touch):
        col_self = self.collide_point(*touch.pos)
        col_side = self._side_panel.collide_point(*touch.pos)
        col_main = self._main_panel.collide_point(*touch.pos)

        if self._anim_progress < 0.001:  # i.e. closed
            valid_region = (self.x <=
                            touch.x <=
                            (self.x + self.touch_accept_width))
            y_valid = (self.y+self.height/2 - self.touch_accept_height/2 <= \
                        touch.y <= self.y+self.height/2 + self.touch_accept_height/2)
            if not valid_region:
                self._main_panel.on_touch_down(touch)
                return False
        else:
            if col_side and not self._main_above:
                self._side_panel.on_touch_down(touch)
                return False
            valid_region = (self._main_panel.x <=
                            touch.x <=
                            (self._main_panel.x + self._main_panel.width))
            y_valid = (self.y+self.height/2 - self.touch_accept_height/2 <= \
                        touch.y <= self.y+self.height/2 + self.touch_accept_height/2)
            if not valid_region and not y_valid:
                if self._main_above:
                    if col_main:
                        self._main_panel.on_touch_down(touch)
                    elif col_side:
                        self._side_panel.on_touch_down(touch)
                else:
                    if col_side:
                        self._side_panel.on_touch_down(touch)
                    elif col_main:
                        self._main_panel.on_touch_down(touch)
                return False
        Animation.cancel_all(self)
        self._anim_init_progress = self._anim_progress
        self._touch = touch
        touch.ud['type'] = self.state
        touch.ud['panels_jiggled'] = False  # If user moved panels back
                                            # and forth, don't default
                                            # to close on touch release
        touch.grab(self)
        return True



class SocialHomeWidget(Widget):
    '''Manages Creen Widgets With Application Drawer'''

    app = ObjectProperty(None)
    initialized = BooleanProperty(False)
    tab_height_frac = NumericProperty( 0.15)
    
    def __init__(self, app, **kwargs):
        super(SocialHomeWidget,self).__init__(**kwargs)
        self.app = app

        self.setupMenu(**kwargs)
        self.setupAppPanel()
        self.initialize()
        
        #Callbacks
        self.bind(pos =  self.update_rect,
                  size = self.update_rect)

    def setupMenu(self,**kwargs):
        self.menu = SocialNavigationBar(side_panel_width=0,**kwargs)
        self.menu.anim_type = 'slide_above_anim'
        self.menu.side_panel_width = 100
        with self.menu.canvas.after:
            Color(rgba=(0.9,0.9,0.9,1))
            self.ribbon = Rectangle(
                        source= RIBBON_ICON,
                        size= (170.0*self.tab_height_frac,930.0*self.tab_height_frac),
                        pos= (self.x+self.menu._side_panel.width - 170.0*self.tab_height_frac/2,\
                             self.y+self.menu._side_panel.height*0.5-930.0*self.tab_height_frac/2))
        self.menu._side_panel.bind(x = self.update_tab_image)

        self.add_widget( self.menu )

    def initialize(self):
        print 'default init'
        pass

    def setupAppPanel(self):
        #First Widget Added To Menu Is The Actual Menu
        self.menu_panel = MenuPanel()
        self.menu.add_widget(self.menu_panel)

        #The Second Added Is For the Main Widget
        self.menuScreenManager = ScreenManager(transition=SwapTransition())
        self.menu.add_widget(self.menuScreenManager)

    def addMenuScreenWidget(self,name,button,new_widget,**kwargs):
        #Add Menu Button
        iconentry = BoxLayout(orientation='vertical',spacing=20)
        iconentry.add_widget(Label(text=name.capitalize(),**kwargs))
        iconentry.add_widget(button)

        self.menu_panel.add_widget(iconentry)
        button.bind( on_press = lambda *args: self.changeScreen(name) )

        #Add The Widget Itself
        screen = Screen(name = name)
        screen.add_widget(new_widget)

        self.menuScreenManager.add_widget(screen)

    def changeScreen(self,screenName):
        self.menuScreenManager.current = screenName

    def update_rect(self,*args):
        self.menu.size = self.size
        self.ribbon.size= (170.0*self.tab_height_frac,930.0*self.tab_height_frac)
        self.ribbon.pos= (self.menu._side_panel.x+self.menu._side_panel.width - 170.0*self.tab_height_frac/2,\
                             self.y+self.menu._side_panel.height*0.5-930.0*self.tab_height_frac/2)

    def update_tab_image(self,*args):
        self.ribbon.size= (170.0*self.tab_height_frac,930.0*self.tab_height_frac)
        self.ribbon.pos= (self.menu._side_panel.x+self.menu._side_panel.width - 170.0*self.tab_height_frac/2,\
                             self.y+self.menu._side_panel.height*0.5-930.0*self.tab_height_frac/2)


app = None

if __name__ == '__main__':

    font_opts = dict(size_hint=(1,1),
                        color=(0,0,0,1),text_size=(100,None),\
                        valign='bottom',halign='center',
                        font_size=20,
                        font_name=os.path.join('fonts','Monument_Valley_1.2-Regular.ttf'))
    icon_opt = dict(size_hint=(0.75,1))
    but_opt = dict(color_normal=(1,1,1,1),color_down=BUTTONDOWN,\
                    border_color=SECONDARY_COLOR,radius=0,\
                    color=(0,0,0,1),size_hint=(1,1),border_width=2,\
                    font_size=20,font_name=os.path.join('fonts','Monument_Valley_1.2-Regular.ttf'))


    class PrjApp(App):

        #Full Menu Layout .. takes a while to load.. not great for dev
        def build(self):
            self.socialHome = SocialHomeWidget( self, touch_accept_width=50)



            profile = MenuBar(self)
            for screen in ('overview','roles','projects','messages'):
                print screen
                if screen == 'overview':
                    profile.addMenuScreenWidget(screen,UserListView(),**but_opt)
                elif screen == 'messages':
                    profile.addMenuScreenWidget(screen,UserListView(),**but_opt)
                else:
                    profile.addMenuScreenWidget(screen,FeatureListView(),**but_opt)

            projects = MenuBar(self)
            for screen in ('map','nearby','your projects','make'):
                print screen
                if screen == 'map':
                    projects.addMenuScreenWidget(screen,MapWidget(self),**but_opt)
                elif screen == 'your projects':
                    project_view = MenuTabSlider(self,size_hint=(1,1))
                    for _screen in ('overview','crew chat','crew list','auditions','edit'):
                        if _screen in ('crew list','crew chat','auditioins'):
                            project_view.addMenuScreenWidget(_screen,UserListView())
                        else:
                            project_view.addMenuScreenWidget(_screen,FeatureListView())
                    projects.addMenuScreenWidget(screen,project_view,**but_opt)
                else:
                    projects.addMenuScreenWidget(screen,FeatureListView(),**but_opt)

            casting = MenuBar(self)
            for screen in ('map','nearby','your roles','make'):
                print screen
                if screen == 'map':
                    casting.addMenuScreenWidget(screen,MapWidget(self),**but_opt)
                elif screen == 'nearby':
                    casting.addMenuScreenWidget(screen,FeatureListView(),**but_opt)
                elif screen == 'your roles':
                    role_view = MenuTabSlider(self,size_hint=(1,1))
                    for _screen in ('overview','canidates','applicants','invite'):
                        if _screen in ('canidates','applicants'):
                            role_view.addMenuScreenWidget(_screen, UserListView())
                        else:
                            role_view.addMenuScreenWidget(_screen,FeatureListView())
                    casting.addMenuScreenWidget(screen,role_view,**but_opt)
                else:
                    casting.addMenuScreenWidget(screen,UserListView(),**but_opt)

            self.socialHome.addMenuScreenWidget('profile',CircularIcon(source=os.path.join('icons','award_gold.png'),**icon_opt)\
                                                         ,profile,**font_opts)
            self.socialHome.addMenuScreenWidget('projects',CircularIcon(source=os.path.join('icons','camcorder.png'),**icon_opt)\
                                                        ,projects,**font_opts)
            self.socialHome.addMenuScreenWidget('casting',CircularIcon(source=os.path.join('icons','bullhorn.png'),**icon_opt)\
                                                        ,casting,**font_opts)
            self.socialHome.addMenuScreenWidget('camera',CircularIcon(source=os.path.join('icons','photo-camera.png'),**icon_opt)\
                                                        ,Widget(),**font_opts)
#            self.socialHome.addMenuScreenWidget('club',CircularIcon(source=os.path.join('icons','icon.png'),**icon_opt)\
#                                                        ,Widget(),**font_opts)
            self.socialHome.addMenuScreenWidget('',RoundedButton(text='logout',**but_opt),Widget())
            return self.socialHome
#
#        def build(self):
#            anc = AnchorLayout(size_hint = (1,1))
#            mt = MenuTabSlider(self,size_hint=(1,1))
#            for i in range(7):
#                mt.addMenuScreenWidget(name = 'profile',new_widget=UserListView())
#
##            anc.add_widget(mt)
##            return anc
#            return mt


    global app
    app = PrjApp()
    app.run()