from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListView
from kivy.uix.carousel import Carousel
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.image import *
from kivy.uix.button import *
from kivy.uix.behaviors import *
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.effectwidget import *

from kivy.garden.mapview import MarkerMapLayer, MapLayer, MapMarker
from kivy.garden.smaa import SMAA

import json

from kivy.properties import *

from style import *
from maps import *
from config import *
from social_interface import *

path = EXP_PATH

class ProfileData(object):
    '''Profile Loading Functionality'''

    user_dict = ObjectProperty(None)
    images = ListProperty(None)
    info = StringProperty(None)
    name = StringProperty(None)
    location = ListProperty(None)

    def loadDataFromServer(self, user_id, method = 'get_user_info'):
        app = App.get_running_app()
        self.d = app.social_client.perspective.callRemote('get_user_info',user_id)
        self.d.addCallback(self.createFromJson)
        self.d.addCallback(self.initialize)
        return self.d

    def createFromJson(self,user_json):
        print user_json
        self.user_dict = json.loads(user_json)
        self.images = self.user_dict['images']
        self.info = self.user_dict['info']
        self.name = self.user_dict['name']
        self.location = self.user_dict['location']

    def initialize(self,*args):
        pass


class ProfileView(Widget,ProfileData):

    def __init__(self, user_id,**kwargs):
        super(ProfileView,self).__init__(**kwargs)
        #Remote Call Server, Defer Creation Of Widgets
        self.loadDataFromServer(user_id)

    def initialize(self,*args):

        user_info = ListAdapter(data= self.info.split('\n'),\
                                cls = Label)
        #Define Layout
        self._layout = BoxLayout( orientation = 'vertical' )
        self._name = Label( text = self.name.upper(), \
                            font_name= HEADER_FONT,
                            valign = 'bottom', size_hint = (1,0.15),
                            font_size=38, bold=True,)
        #self._image = RoundedImage( source = image_url)
        #                            #allow_stretch=True)
        self._image = RoundedWebImage(source = self.images[0])
        self._info = ListView( adapter = user_info, size_hint = (1,0.6) )

        self._layout.add_widget(self._name)
        self._layout.add_widget(self._image)
        self._layout.add_widget(self._info)

        self.add_widget(self._layout)

        self.bind(pos = self.update_rect,
                  size = self.update_rect)

    def update_rect(self,*args):
        self._layout.pos = self.pos
        self._layout.size = self.size

class ProfileEditView(Widget,ProfileData):

    def __init__(self,user_id,**kwargs):
        super(ProfileEditView,self).__init__(**kwargs)

    def initialize(self,*args):

        user_info = ListAdapter(data= self.info.split('\n'),\
                                cls = Label)
        #Define Layout
        self._layout = BoxLayout( orientation = 'vertical' )
        self._name = Label( text = self.name.upper(), \
                            font_name= HEADER_FONT,
                            valign = 'bottom', size_hint = (1,0.15),
                            font_size=38, bold=True,)
        #self._image = RoundedImage( source = image_url)
        #                            #allow_stretch=True)
        self._image = RoundedWebImage(source = self.images[0])
        self._info = ListView( adapter = user_info, size_hint = (1,0.6) )

        self._layout.add_widget(self._name)
        self._layout.add_widget(self._image)
        self._layout.add_widget(self._info)

        self.add_widget(self._layout)

        self.bind(pos = self.update_rect,
                  size = self.update_rect)



class ProfileButton(ButtonBehavior,Widget,ProfileData):

    def __init__(self, user_id,**kwargs):
        self.target_func = kwargs.pop('target_func', lambda: None)
        self.bind(on_press = self.target_func)

        Widget.__init__(self,**kwargs)
        ButtonBehavior.__init__(self,**kwargs)
        self.loadDataFromServer(user_id)


    def on_press(self):
        print 'calling target_func'
        self.target_func()

    def initialize(self,*args):
        #Define Layout
        self._layout = BoxLayout( orientation = 'vertical' )
        self._name = Label( text = self.name.upper(), \
                            font_name= HEADER_FONT,
                            valign = 'bottom', size_hint = (1,0.25),
                            font_size=25, bold=True,)
        self._image = CircleWebImage(source = self.images[0])

        self._layout.add_widget(self._name)
        self._layout.add_widget(self._image)

        self.add_widget(self._layout)

        self.bind(pos = self.update_rect,
                  size = self.update_rect)

    def update_rect(self,*args):
        self._layout.pos = self.pos
        self._layout.size = self.size


Builder.load_string("""
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
""")

class ProfileMapIcon(AsyncMapMarker,ProfileData):
    effects = [HorizontalBlurEffect(size=1), VerticalBlurEffect(size=1), FXAAEffect()]
    def __init__(self,maps,user_id,**kwargs):
        super(ProfileMapIcon,self).__init__()
        self.maps = maps

        d = self.loadDataFromServer(user_id)
        d.addCallback(self.setData)

    def setData(self,*args):
        self.source = self.images[-1]
        self.lat = self.location[0]
        self.lon = self.location[1]
        print 'adding at {},{}'.format(self.lat,self.lon)
        self.maps.map.add_marker(self)

class SwipingWidget(Widget):

    canidates = ListProperty(None)

    def __init__(self, app):
        super(SwipingWidget,self).__init__()
        self.app = app

        self.swiper = Carousel(direction='right')

        self.add_widget(self.swiper)

        self.bind(pos= self.update_rect,
                  size = self.update_rect)

    def updateNearby(self,local_users):
        if local_users:
            self.canidates = []
            for user_id in local_users:
                self.canidates.append(user_id)
                profile = ProfileView(user_id)
                self.swiper.add_widget(profile)

    def update_rect(self,*args):
        self.swiper.size = self.size


if __name__ == '__main__':
    from kivy.config import Config
    iphone =  {'width':320 , 'height': 568}#320 x 568

    def setWindow(width,height):
        print 'Setting Window'
        Config.set('graphics', 'width', str(width))
        Config.set('graphics', 'height', str(height))

    class ProfilesApp(SocialApp):

        def setupMainScreen(self):
            swiper = Carousel(direction='right')

            profile = ProfileButton(user_id = 1)
            swiper.add_widget(profile)
            from kivy.core.window import Window
            Window.size = (iphone['width'],iphone['height'])

            return swiper

    profileApp = ProfilesApp()
    profileApp.run()
