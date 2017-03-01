# -*- coding: utf-8 -*-
"""
Created on Sat Feb 18 22:56:33 2017

@author: Cabin
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import *
from kivy.garden.androidtabs import *
from kivy.lang.builder import *

Builder.load_string(
'''
<-AndroidTabsUnder@AndroidTabs>:
    carousel: carousel
    tab_bar: tab_bar
    anchor_y: 'bottom'
    
    tab_indicator_color: 177/255.,144/255.,70/255.,1
    text_color_normal: 1,1,1,1
    text_color_active: 177/255.,144/255.,70/255.,1   
    AndroidTabsMain:
        padding: 0, tab_bar.height, 0, 0

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

                canvas.after:
                    Color:
                        rgba: root.tab_indicator_color
                    Rectangle:
                        pos: self.pos
                        size: 0, root.tab_indicator_height 
''')

class AndroidTabsUnder(AndroidTabs):
    pass

class MyTab(Image,AndroidTabsBase):
    source = r'icons\award_gold.png'
    pass


class Example(App):

    def build(self):

        android_tabs = AndroidTabsUnder()
        android_tabs.tab_bar_height = 30
        for n in range(1, 6):   
            tab = MyTab(text='TAB %s' % n)
            android_tabs.add_widget(tab)

        return android_tabs

Example().run()