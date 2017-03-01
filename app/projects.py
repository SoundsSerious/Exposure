# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 19:28:32 2017

@author: Cabin
"""
import os, sys
import random
from glob import glob

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import *
from kivy.uix.scrollview import *
from kivy.uix.boxlayout import *
from kivy.uix.textinput import TextInput
from kivy.uix.image import AsyncImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FallOutTransition, \
                                    FadeTransition, RiseInTransition
from kivy.properties import *
from kivy.clock import Clock
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder

from config import *
from social_interface import *
from maps import *
from style import *

LORN_IPSUM = '''Lorem ipsum dolor sit amet, ut altera adipiscing reformidans his. Ut suas clita epicuri eos. Justo verterem eu pri, autem iudicabit in mea. Id vel alienum fabellas definitionem, ex usu putant corpora copiosae, nam aliquip posidonium no.'''*9


Builder.load_string('''
#:import os os

<-ProjectListEntry@BoxLayout>:
    orientation: "horizontal"
    size_hint_y: None
    height: 100
    canvas:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            size: self.size
            pos: self.pos
        Color:
            rgba: 0,0,0,1
        Line:
            points: self.x,1,self.x,self.x+self.width,1
            width: 1
        Line:
            points: self.x,self.height,self.x,self.x+self.width,self.height
            width: 1

    SquareExpandingWebImage:
        id: image
        source: root.img_source
        size_hint: (None,0.95)
        pos_hint: {'center_x':0.5,'center_y':0.5}
        width: 100
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.8
        height: 30
        Label:
            color: 0,0,0,1
            font_size: 20
            font_name: 'fonts/Monument_Valley_1.2-Regular.otf'
            id: title
            text: root.title_text.upper()
            size_hint_y: 0.25
        Label:
            id: body
            color: 0,0,0,1
            text: root.body_text
            size_hint_y:0.9
            font_size: 10
            text_size: (self.width * 0.75, self.height)
            halign: 'left'
            valign: 'top'
            font_name: 'fonts/Quicksand-Regular.otf'
    BoxLayout:
        orientation:'vertical'
        id: button_bar
        width: 25
        size_hint_x: None

<PublicMapView@DragBehavior>:
    height: 300
    width: 225
    size_hint: (None,None)
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_timeout: 10000000
    drag_distance: 0
    canvas.before:
        Color:
            rgb: (1, 1, 1)

        StencilPush
        RoundedRectangle:
            size: (self.width,self.height-self.tri_height)
            pos: self.center[0] - self.width/2.0,self.center[1] - self.height/2.0+self.tri_height
            radius: self.radius
        StencilUse

    canvas:
        Color:
            rgba: (1, 1, 1, 1)
        RoundedRectangle:
            size: (self.width,self.height-self.tri_height)
            pos: self.center[0] - self.width/2.0,self.center[1] - self.height/2.0+self.tri_height
            radius: self.radius
            
    canvas.after:
        StencilUnUse
        RoundedRectangle:
            size: (self.width,self.height-self.tri_height)
            pos: self.center[0] - self.width/2.0,self.center[1] - self.height/2.0+self.tri_height
            radius: self.radius
        StencilPop
        Color:
            rgba: (1, 1, 1, 1)
        Triangle:
            points: (self.center[0]-self.tri_width,self.y+self.tri_height,\
                     self.center[0]+self.tri_width,self.y+self.tri_height,\
                     self.center[0],self.y)

    ScrollView:
        size_hint: (0.95,0.95)
        size: (root.width,root.height-root.tri_height)
        pos: root.center[0] - root.width/2.0,root.center[1] - root.height/2.0+root.tri_height
        GridLayout:
            id:layout
            cols: 1
            spaceing: 3
            size_hint_y: None
            size: root.size
            Label:
                id: title
                color: 0,0,0,1
                font_size: 20
                font_name: 'fonts/Monument_Valley_1.2-Regular.otf'                
                text: root.title_text.upper()
                height: 30
                size_hint_y: None
            RoundedExpandingImage:
                id: image
                source: root.img_source
                height: 200
                size_hint_y: None
                radius: root.radius
            Label:
                id: body
                color: 0,0,0,1
                text: root.body_text
                font_size: 10
                height: self.texture_size[1]
                size_hint_y: None
                text_size: (self.width*0.9, None)
                pos_hint: {'bottom':1}
                halign: 'left'
                valign: 'top'
                font_name: 'fonts/Quicksand-Regular.otf'

<DetailedPublicView>:
    canvas:
        Color:
            rgba: (1, 1, 1, 1)
        Rectangle:
            size: self.size
            pos: self.pos
    ScrollView:
        size_hint: (1,None)
        size: root.size
        GridLayout:
            id:layout
            cols: 1
            spaceing: 3
            size_hint_y: 1
            size: root.size
            Label:
                color: 0,0,0,1
                font_size: 20
                font_name: os.path.join('fonts','Monument_Valley_1.2-Regular')
                id: title
                text: root.title_text.upper()
                height: 30
                size_hint_y: None
            SquareExpandingWebImage:
                id: image
                source: root.img_source
                height: 200
                size_hint_y: None
            Label:
                id: body
                color: 0,0,0,1
                text: root.body_text
                font_size: 10
                height: self.texture_size[1]
                size_hint_y: None
                text_size: (self.width*0.9, None)
                pos_hint: {'bottom':1}
                halign: 'left'
                valign: 'top'
                font_name: 'fonts/Quicksand-Regular.otf'

<-ProfileMapIcon>:
    size_hint: None, None
    source: root.source
    size: [20,20]
    allow_stretch: True

    canvas:
        Color:
            rgb: 1,1,1
        Ellipse:
            pos: self.pos
            size: min(self.size),min(self.size)
        StencilPush
        Ellipse:
            pos: self.pos[0]+1,self.pos[1]+1,
            size: min(self.size)-2,min(self.size)-2
        StencilUse
        Rectangle:
            texture: self.texture
            pos: self.pos
            size: self.size
        StencilUnUse
        Ellipse:
            pos: self.pos
            size: min(self.size)-2,min(self.size)-2
        StencilPop
        
<ProjectListView>:
    background_color: [1,1,1,1]
    size_hint: 1,1
    shadow_frac: 0.05
    canvas:
        Color:
            rgba: 0.7,0.7,0.7,1
        Rectangle:
            source: os.path.join('resources','background.jpg')
            size: self.size
            pos: self.pos
    canvas.after:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            source:os.path.join('resources','vert_trans.png')
            size: self.width, self.height*self.shadow_frac
            pos: self.x,self.y+self.height*(1-self.shadow_frac)
            '''
)


    
#Add This To Classes Later... Like Profile... Maybe Common Interface
class ProjectData(NetworkData):
    '''Profile Loading Functionality'''

    user_dict = ObjectProperty(None)
    images = ListProperty(None)
    info = StringProperty('')
    name = StringProperty('')
    location = ListProperty(None)

    def on_primary_key(self,inst,val):
        app = App.get_running_app()
        self.d = app.social_client.perspective.callRemote('get_project_info',self.primary_key)
        self.d.addCallbacks(self.createFromJson, self.catchError)
        return self.d

    def createFromJson(self,user_json):
        if user_json:
            self.user_dict = json.loads(user_json)
            self.images = self.user_dict['images']
            self.info = self.user_dict['info']
            self.name = self.user_dict['name']
            self.location = self.user_dict['location']
            self.initialize()
    
class ProjectMapIcon(AsyncMapMarker,ProjectData):

    def __init__(self,maps,project_id,**kwargs):
        super(ProjectMapIcon,self).__init__(**kwargs)
        self.maps = maps
        self.primary_key = project_id

    def initialize(self):
        self.source = self.images[-1]
        self.lat = self.location[0]
        self.lon = self.location[1]
        print 'adding at {},{}'.format(self.lat,self.lon)
        self.maps.map.add_marker(self)    

class PublicMapView(DragBehavior,Widget,ProjectData):
    radius = ListProperty([20])
    tri_width = 20
    tri_height= 10

    title_text = StringProperty('')
    img_source = StringProperty('')
    body_text = StringProperty('')    
    
    def __init__(self,project_id,**kwargs):
        super(PublicMapView,self).__init__(**kwargs)
        self.primary_key = project_id
        self.ids['layout'].bind(minimum_height=self.ids['layout'].setter('height'))
        
    
    def initialize(self,**kwargs):
        self.img_source = self.images[-1]
        self.title_text = self.name
        self.body_text = self.info
    
    def on_img_source(self,*args):
        print self.img_source
        self.ids['image'].source = self.img_source

    def on_title_text(self,*args):
        self.ids['title'].text = self.title_text

    def on_body_text(self,*args):
        self.ids['body'].text = self.body_text        
        
        
class DetailedPublicView(Widget,ProjectData):    
    title_text = StringProperty('')
    img_source = StringProperty('')
    body_text = StringProperty(LORN_IPSUM)    

    def __init__(self,project_id,**kwargs):
        super(DetailedPublicView,self).__init__(**kwargs)
        self.primary_key = project_id
        self.ids['layout'].bind(minimum_height=self.ids['layout'].setter('height'))
        
    def initialize(self,**kwargs):
        self.img_source = self.images[-1]
        self.title_text = self.name
        self.body_text = self.info
        
    def on_img_source(self,*args):
        print self.img_source
        self.ids['image'].source = self.img_source

    def on_title_text(self,*args):
        self.ids['title'].text = self.title_text

    def on_body_text(self,*args):
        self.ids['body'].text = self.body_text             

class ProjectListEntry(ButtonBehavior,BoxLayout,ProjectData):
    
    title_text = StringProperty('')
    img_source = StringProperty('')
    body_text = StringProperty('')

    def __init__(self,project_id,**kwargs):
        super(ProjectListEntry,self).__init__(**kwargs)
        self.primary_key = project_id

    def add_button_icon(self,iconImage,callback,width=25):
        ic = Icon(source=iconImage,size_hint=(None,None),width=width)
        ic.bind(on_press = callback)
        self.ids['button_bar'].add_widget(ic)
        self.ids['button_bar'].width = width+5
        
    def initialize(self,**kwargs):
        self.img_source = self.images[-1]
        self.title_text = self.name
        self.body_text = self.info
        
    def on_img_source(self,*args):
        print self.img_source
        self.ids['image'].source = self.img_source

    def on_title_text(self,*args):
        self.ids['title'].text = self.title_text.upper()

    def on_body_text(self,*args):
        self.ids['body'].text = self.body_text         
        

class ProjectListView(Widget):

    def __init__(self,**kwargs):
        super(ProjectListView,self).__init__(**kwargs)
        self.layout = GridLayout(cols=1, spacing=3, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))


        for i,prj in enumerate(PROJECTS):
            pw = ProjectListEntry(i+1)
            pw.add_button_icon(ADDUSER_ICON,hello)
            self.layout.add_widget(pw)

        self.scroll = ScrollView(size_hint=(1, None))
        self.scroll.add_widget(self.layout)
        self.add_widget(self.scroll)

        self.bind(size=self.update_rect)

    def update_rect(self,*args):
        self.scroll.size = self.size




if __name__ == '__main__':

    font_opts = dict(size_hint=(1,0.9),
                        color=(0,0,0,1),text_size=(100,None),\
                        valign='top',halign='center',
                        font_size=20,
                        font_name=os.path.join('fonts','Monument_Valley_1.2-Regular.ttf'))
    
    icon_opt = dict(size_hint=(0.75,1))
    
    but_opt = dict(color_normal=(1,1,1,1),color_down=(0.9,0.9,0.9,1),\
                    border_color=(177/255.,144/255.,70/255.,1),radius=5,\
                    color=(0,0,0,1),size_hint=(0.8,0.05),border_width=2,\
                    pos_hint = {'center_x':0.5},\
                    font_size=20,font_name=os.path.join('fonts','Monument_Valley_1.2-Regular.ttf'))


    class PrjApp(SocialApp):

        def setupMainScreen(self):
            lay = FloatLayout()
            with lay.canvas:
                rect = Rectangle(size=lay.size,color=(1,1,1,1))
                def update_lay(inst,val):
                    rect.size = inst.size
            lay.bind(size = update_lay)
            lay.add_widget( MapWidget(self))
            lay.add_widget(PublicMapView(1))
            lay.add_widget( PublicMapView(2))
            lay.add_widget(FeatureListView())
            lay.add_widget( RoundedButton(text='Apply',**but_opt))
            mp = MapWidget(self)
            
            return DetailedPublicView(2)


    PrjApp().run()

