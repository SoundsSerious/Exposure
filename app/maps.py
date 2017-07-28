from kivy.garden.mapview import *
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.graphics.vertex_instructions import *
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import *
from kivy.uix.image import *
from kivy.garden.androidtabs import *
from kivy.core.window import Window
from kivy.animation import Animation
import copy
from kivy.uix.widget import Widget
from kivy.properties import *

from numpy import interp

from config import *
from social_interface import *




class AsyncMapMarker(ButtonBehavior, AsyncImage):
    """A marker on a map, that must be used on a :class:`MapMarker`
    """

    anchor_x = NumericProperty(0.5)
    """Anchor of the marker on the X axis. Defaults to 0.5, mean the anchor will
    be at the X center of the image.
    """

    anchor_y = NumericProperty(0)
    """Anchor of the marker on the Y axis. Defaults to 0, mean the anchor will
    be at the Y bottom of the image.
    """

    lat = NumericProperty(0)
    """Latitude of the marker
    """

    lon = NumericProperty(0)
    """Longitude of the marker
    """

    source = StringProperty(None)
    """Source of the marker, defaults to our own marker.png
    """

    # (internal) reference to its layer
    _layer = None

    def detach(self):
        if self._layer:
            self._layer.remove_widget(self)
            self._layer = None

class MapViewRecycleLayer(MarkerMapLayer,AbstractNetworkList):
    '''Container To Hold Primary Keys, And Update A Map Layer'''
    maps = ObjectProperty(None)
    icon_template = ObjectProperty(AsyncMapMarker)

    icon_zfull,icon_zfull_side = 16,80
    icon_zmin,icon_zmin_side = 11,30

    def __init__(self,maps,**kwargs):
        self.maps = maps
        self.icon_template = kwargs.get('template',self.icon_template)

        super(MapViewRecycleLayer,self).__init__(**kwargs)
        AbstractNetworkList.__init__(self,**kwargs)

        self.maps.map.add_layer(self)

    def reposition(self):
        if self.markers:
            super(MapViewRecycleLayer,self).reposition()
            side = interp(  self.maps.map.zoom,\
                            [self.icon_zmin,self.icon_zfull],\
                            [self.icon_zmin_side,self.icon_zfull_side])
            size = (side,side)
            for marker in self.markers:
                anim = Animation(size=size,duration= 0.25,t='out_quad')
                anim.start(marker)


    def on_primary_keys(self,inst,val):
        for mrk in self.markers:
            self.remove_widget(mrk)
        self.markers = []
        for i in val:
            self.icon_template(layer = self,primary_key=i)

class DragNDropWidget(Widget):
    # let kivy take care of kwargs and get signals for free by using
    # properties
    droppable_zone_objects = ListProperty([])
    bound_zone_objects = ListProperty([])
    drag_opacity = NumericProperty(1.0)
    drop_func = ObjectProperty(None)
    drop_args = ListProperty([])
    remove_on_drag = BooleanProperty(True)

    def __init__(self, **kw):
        super(DragNDropWidget, self).__init__(**kw)

        self.register_event_type("on_drag_start")
        self.register_event_type("on_being_dragged")
        self.register_event_type("on_drag_finish")
        self.register_event_type("on_motion_over")
        self.register_event_type("on_motion_out")

        self._dragged = False
        self._dragable = True
        self._fired_already = False

    def set_dragable(self, value):
        self._dragable = value

    def set_remove_on_drag(self, value):
        """
        This function sets the property that determines whether the dragged widget is just copied from its parent or taken from its parent
        @param value: either True or False. If True then the widget will disappear from its parent on drag, else the widget will jsut get copied for dragging
        """
        self.remove_on_drag = value

    def set_bound_axis_positions(self):
        for obj in self.bound_zone_objects:
            try:
                if self.max_y < obj.y+obj.size[1]-self.size[1]:
                    self.max_y = obj.y+obj.size[1]-self.size[1]
            except AttributeError:
                self.max_y = obj.y+obj.size[1]-self.size[1]
            try:
                if self.max_x < obj.x+obj.size[0]-self.size[0]:
                    self.max_x = obj.x + obj.size[0]-self.size[0]
            except AttributeError:
                self.max_x = obj.x+obj.size[0]-self.size[0]
            try:
                if self.min_y > obj.y:
                    self.min_y = obj.y
            except AttributeError:
                self.min_y = obj.y
            try:
                if self.min_x > obj.x:
                    self.min_x = obj.x
            except AttributeError:
                self.min_x = obj.x

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y) and self._dragable:
            # detect if the touch is short - has time and end (if not dispatch drag)
            if abs(touch.time_end - touch.time_start) > 0.2:
                self.dispatch("on_drag_start")


    def on_touch_up(self, touch):
        if self._dragable and self._dragged:
            self.short_touch = True
            self.dispatch("on_drag_finish")
            self.short_touch = False

    def on_touch_move(self, touch):
        if self._dragged and self._dragable:
            x = touch.x
            y = touch.y

            try:
                if touch.x < self.min_x:
                    x = self.min_x
                if touch.x > self.max_x:
                    x = self.max_x
                if touch.y < self.min_y:
                    y = self.min_y
                if touch.y > self.max_y:
                    y = self.max_y
            except AttributeError:
                pass
            self.pos = (x, y)

    def easy_access_dnd(self, function_to_do, function_to_do_out, arguments = [], bind_functions = []):
        """
        This function enables something that can be used instead of drag n drop
        @param function_to_do: function that is to be called when mouse_over event is fired on the widget
        @param bind_functions: what is really to be done - background function for GUI functionality
        """
        Window.bind(mouse_pos=self.on_motion)
        self.easy_access_dnd_function = function_to_do
        self.easy_access_dnd_function_out = function_to_do_out
        self.easy_access_dnd_function_aguments = arguments
        self.easy_access_dnd_function_binds = bind_functions

    def on_motion(self, etype, moutionevent):
        if self.collide_point(Window.mouse_pos[0], Window.mouse_pos[1]):
            if not self._fired_already:
                self.dispatch("on_motion_over")
        else:
            self.dispatch("on_motion_out")

    def on_motion_over(self):
        self.easy_access_dnd_function(
            self.easy_access_dnd_function_aguments,
            self.easy_access_dnd_function_binds)

        self._fired_already = True

    def on_motion_out(self):
        try:
            self.easy_access_dnd_function_out()
        except AttributeError:
            pass
        self._fired_already = False

    def on_drag_start(self):
        self.opacity = self.drag_opacity
        self.set_bound_axis_positions()
        #self._old_drag_pos = copy.copy(self.pos)
        self._old_parent = self.parent
        self._old_index = self.parent.children.index(self)
        self._dragged = True
        if self.remove_on_drag:
            self.reparent(self)
        else:
            #create copy of object to drag
            self.reparent(self)
            # the final child class MUST implement __deepcopy__
            # IF self.remove_on_drag == False !!! In this case this is
            # met in DragableArhellModelImage class
            copy_of_self = copy.deepcopy(self)
            self._old_parent.add_widget(copy_of_self, index=self._old_index)

    def on_drag_finish(self):
        if self._dragged and self._dragable:
            self.opacity = 1.0
            dropped_ok = False
            for obj in self.droppable_zone_objects:
                if obj.collide_point(*self.pos):
                    dropped_ok = True
            if dropped_ok:
                self.drop_func(*self.drop_args)
#                anim = Animation(opacity=0, duration=0.7, t="in_quad")
#                anim.bind(on_complete=self.deparent)
#                anim.start(self)
                #print 'Dropped Back To {} from {}'.format(self._old_drag_pos,self.pos)
                anim = Animation(pos=self._old_drag_pos, duration=0.5, t="in_quad")
                if self.remove_on_drag:
                    anim.bind(on_complete = self.reborn)
                else:
                    anim.bind(on_complete = self.deparent)
                anim.start(self)
            else:
                #print 'Going Back To {} from {}'.format(self._old_drag_pos,self.pos)
                anim = Animation(pos=self._old_drag_pos, duration=0.5, t="in_quad")
                if self.remove_on_drag:
                    anim.bind(on_complete = self.reborn)
                else:
                    anim.bind(on_complete = self.deparent)
                anim.start(self)
            self._dragged = False

    def deparent(self, widget="dumb", anim="dumb2"):
        self.get_root_window().remove_widget(self)

    def on_being_dragged(self):
        print "being dragged"

    def reborn(self, widget, anim):
        self.deparent()
        self._old_parent.add_widget(self, index=self._old_index)

    def reparent(self, widget):
        parent = widget.parent
        orig_size = widget.size
        if parent:
            parent.remove_widget(widget)
            parent.get_root_window().add_widget(widget)
            widget.size_hint = (None, None)
            widget.size = orig_size

from kivy.uix.button import Button


class DragableButton(Button, DragNDropWidget):
    '''
    classdocs
    '''
    def __init__(self, **kw):
        '''
        Constructor
        '''
        #Button.__init__(self, **kw)
        super(DragableButton, self).__init__(**kw)
        self.size_hint = (None, None)

    def __deepcopy__(self, dumb):
        return DragableButton(text=self.text,
                              droppable_zone_objects=self.droppable_zone_objects,
                              bound_zone_objects=self.bound_zone_objects,
                              drag_opacity=self.drag_opacity,
                              drop_func=self.drop_func,
                              remove_on_drag=self.remove_on_drag)

Builder.load_string('''
<-ShootWidget>
    canvas:
        Clear

<-MyTab>:
    canvas:
        Color:
            rgb: 0.1,0.5,1
        Ellipse:
            size: 50,50#min(self.size),min(self.size)
            pos: self.center#[0] - min(self.size)/2,10+self.center[1] - min(self.size)/2,
''')

class ShootWidget(DragableButton):
    '''In which we define behavior for a shoot instance drop

    Must Specify:
    inital_pos = (x,y)'''

    _inital_pos = None
    _icon_size = (30,30)
    _img_size = (25,25)
    #_lens_size = (8,8)
    _icon_mrg = 1
    _map_widg = None

    def __init__(self, **kwargs):
        super(ShootWidget,self).__init__(size = self._icon_size,**kwargs)
        self.pos = self.initial_pos = kwargs.get('inital_pos',(0,0))

        self._map_widg = kwargs.get('map',None)
        self.droppable_zone_objects = [ self.map ]

        self.drag_opacity = 0.5
        self.drop_func = self.drop_it

        with self.canvas:
            Color(1,1,1)

            self._ring = Ellipse(pos = self.pos,size=self._icon_size)
            self._apeture = Rectangle(pos = self.img_pos, \
                                      size= self._img_size,\
                                      source = os.path.join(APP_PATH,'icons','tiny_apeture.png'))

            #Ellipse(pos = self.lens_pos,size=self._lens_size)

        self.bind(pos = self.update_canvas,
                  size = self.update_canvas)

    def update_canvas(self,*args):
        self._ring.pos = self.pos
        self._apeture.pos = self.img_pos

    @property
    def map(self):
        return self._map_widg

    @property
    def img_pos(self):
        mrg = ((self._icon_size[0] - self._img_size[0])/2,
               (self._icon_size[1] - self._img_size[1])/2)
        return (self.pos[0] + mrg[0],self.pos[1] + mrg[1])


    @property
    def initial_pos(self):
        return self._inital_pos

    @initial_pos.setter
    def initial_pos(self, val):
        if type(val) is tuple and len(val) == 2:
            self._inital_pos = val[0] - self.size[0]/2.0, val[1] - self.size[1]/2.0
            #Override Drop Widget Parameters
            self._old_drag_pos = self._inital_pos
            self.pos = self._inital_pos

    def drop_it(self):
        coord = self.map.get_latlon_at(*self.pos)
        marker = MapMarker(lat = coord.lat,lon = coord.lon)
        self.map.add_marker(marker)






class MyTab(BoxLayout, AndroidTabsBase):
    pass



class MapWidget(Widget):
    '''In Which We Define A Map View With Interactivity'''
    _map = None
    _layout = None
    _menu = None

    _shoot_btn_height = 15

    def __init__(self,app, lat=26.7153, lon= -80.05, zoom = 11, **kwargs):
        super(MapWidget, self).__init__(**kwargs)

        self.app = app
        self._layout = FloatLayout()

        self._map = MapView(zoom=zoom, lat=lat, lon=lon,size_hint=(1,1))
        self._map.background_color = [0/255.,0/255.,0/255.,1]
        self._map.map_source = 'dark matter'

        self._shoot = ShootWidget(map = self._map,inital_pos=(self.width/2-self._shoot_btn_height\
                                                ,self._shoot_btn_height*1.5) )


        self._layout.add_widget(self._map)
        self._layout.add_widget(self._shoot)

        self.add_widget(self._layout)

        self.bind(size=self.update_rect,
                  pos = self.update_rect)


    @property
    def map(self):
        return self._map

    def update_rect(self,*args):
        self._layout.size = self.size
        self._layout.pos = self.pos
        self._shoot.initial_pos = (self.width/2-self._shoot_btn_height,\
                                    self._shoot_btn_height*1.5)




if __name__ == '__main__':

    from kivy.app import App

    iphone =  {'width':320 , 'height': 568}#320 x 568

    def setWindow(width,height):
        print 'Setting Window'
        Config.set('graphics', 'width', str(width))
        Config.set('graphics', 'height', str(height))

    class MapViewApp(App):
        def build(self):
            #self.m2 = MapMarker(lat=26.7153, lon= -80.05)
            self.mapw = MapWidget(self,lat=26.7153, lon= -80.05)
            #self.mapw.map.add_marker(self.m2)

            from kivy.core.window import Window
            Window.size = (iphone['width'],iphone['height'])

            return self.mapw


    mapview = MapViewApp()
    mapview.run()