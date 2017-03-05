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
from kivy.lang import Builder
from kivy.properties import *
from kivy.garden.mapview import MarkerMapLayer, MapLayer, MapMarker
from kivy.garden.smaa import SMAA
from kivy.uix.recycleview.views import RecycleDataViewBehavior

import json


from style import *
from maps import *
from config import *
from social_interface import *

path = EXP_PATH

#<UserListView>:
#    background_color: [1,1,1,1]
#    size_hint: 1,1
#    shadow_frac: 0.05
#    canvas:
#        Color:
#            rgba: 0.7,0.7,0.7,1
#        Rectangle:
#            source: os.path.join('resources','background.jpg')
#            size: self.size
#            pos: self.pos
#
#    canvas.after:
#        Color:
#            rgba: 1,1,1,1
#        Rectangle:
#            source: os.path.join('resources','vert_trans.png')
#            size: self.width, self.height*self.shadow_frac
#            pos: self.x,self.y+self.height*(1-self.shadow_frac)

Builder.load_string("""

<-UserListEntry@BoxLayout>:
    orientation: "horizontal"
    size_hint_y: None
    height: 100
    canvas:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            size: self.size
            pos: self.pos
    canvas.after:
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

class ProfileData(NetworkData):
    '''Profile Loading Functionality'''

    user_dict = ObjectProperty(None)
    images = ListProperty(None)
    info = StringProperty(None)
    name = StringProperty(None)
    location = ListProperty(None)

    def on_primary_key(self,*args):
        app = App.get_running_app()
        self.d = app.social_client.perspective.callRemote('get_user_info',self.primary_key)
        self.d.addCallback(self.createFromJson)
        return self.d

    def createFromJson(self,user_json):
        if user_json:
            self.user_dict = json.loads(user_json)
            self.images = self.user_dict['images']
            self.info = self.user_dict['info']
            self.name = self.user_dict['name']
            self.location = self.user_dict['location']
            self.initialize()

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




class UserListEntry(ButtonBehavior,RecycleDataViewBehavior,BoxLayout,ProfileData):

    title_text = StringProperty('')
    img_source = StringProperty('')
    body_text = StringProperty('')

    def __init__(self,**kwargs):
        super(UserListEntry,self).__init__(**kwargs)
        self.primary_key = kwargs.get('primary_key',self.primary_key)

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
        self.ids['image'].source = self.img_source

    def on_title_text(self,*args):
        self.ids['title'].text = self.title_text.upper()

    def on_body_text(self,*args):
        self.ids['body'].text = self.body_text

class UserListView(NetworkListView):

    def __init__(self,**kwargs):
        super(UserListView,self).__init__(**kwargs)
        self.viewclass = UserListEntry


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
