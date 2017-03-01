from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty
from kivy.lang import Builder
import kivy
from kivy.clock import Clock
from datetime import datetime as dt

from kivy.lang import Builder
Builder.load_string('''
<ScrollableLabel>:
    Label:
        markup: True
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        text: root.text
''')


class ScrollableLabel(ScrollView):
    text = StringProperty('')
   
class RingBuffer:
    """ class that implements a not-yet-full buffer """
    def __init__(self,size_max):
        self.max = size_max
        self.data = []

    class __Full:
        """ class that implements a full buffer """
        def append(self, x):
            """ Append an element overwriting the oldest one. """
            self.data[self.cur] = x
            self.cur = (self.cur+1) % self.max
        def get(self):
            """ return list of elements in correct order """
            return self.data[self.cur:]+self.data[:self.cur]

    def append(self,x):
        """append an element at the end of the buffer"""
        self.data.append(x)
        if len(self.data) == self.max:
            self.cur = 0
            # Permanently change self's class from non-full to full
            self.__class__ = self.__Full

    def get(self):
        """ Return a list of elements from the oldest to the newest. """
        return self.data

class BufferLog(ScrollableLabel):

    def __init__(self,app,max_size=100):
        super(BufferLog,self).__init__()
        self.app = app
        self.log = RingBuffer(max_size)
        Clock.schedule_interval(self.update, 0.1)
        
    @property
    def newText(self):
        return '\n'.join(self.log.get())

    def update(self,dt):
        self.text = self.newText
        
    def addText(self, text):
        self.log.append( '[color=#87CEEB]{}||[/color]  [color=#E0FFFF]{}[/color]'\
                            .format(dt.now().utcnow(),str(text)) )        

if __name__ == '__main__':
    class MyApp(App):
        def build(self):
            logApp = BufferLog(self)
            logApp.addText('this is some new text')
            return logApp
            
    MyApp().run()
