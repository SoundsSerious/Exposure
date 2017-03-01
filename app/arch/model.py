# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 18:40:18 2016

@author: Cabin
"""
import os
import hashlib

from contextlib import contextmanager


from sqlalchemy import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

import sqlalchemy_imageattach
from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy_imageattach.stores.fs import FileSystemStore
from sqlalchemy_imageattach.context import store_context

from config import *

path = EXP_PATH

engine = create_engine( ENG_STR )

#engine = create_engine('sqlite://')
metadata = MetaData(engine)
Base = declarative_base(metadata=metadata)
#path = r'/Users/Cabin/Dropbox/workspace/Exposure'
usr_images = os.path.join(path,'user_images')
store = FileSystemStore(usr_images,'http://exposureapp.io/')

Session = sessionmaker()
Session.configure(bind=engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

from datetime import datetime
from geoalchemy2 import *

class UserSpot(Base):
    """Basic Implementation Of Location"""
    __tablename__ = 'user_spot'
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.now())
    geom = Column(Geometry(geometry_type='POINT', srid=-1))
    parent_id = Column(Integer, ForeignKey('user.id'),nullable=True)

class User(Base):
    """User model."""
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    info = Column( Text, nullable=True)
    picture = image_attachment('UserPicture')
    location = relationship('UserSpot')


class UserPicture(Base, Image):
    """User picture model."""
    __tablename__ = 'user_picture'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    user = relationship('User')

    @property
    def object_id(self):
        return int(hashlib.sha1(str(self.user_id)).hexdigest(), 16)

def storeSomeUsers():
    from random import random
    LAT,LONG = 26.7153, -80.053
    with session_scope() as session:
        for fil in os.listdir(usr_images):
            if '.jpg' in fil:

                geo = UserSpot( geom = 'POINT({:3.3f} {:3.3f})'.format(LAT+random(),LONG+random()),\
                                parent_id = None)
                name = fil.replace('.jpg','').replace('.',' ')

                session.add(geo)

                new_user = User(name = name, info= 'stuff\n'*20 )
                if geo.id:
                    print geo.id
                    new_user.location = geo.id
                session.add(new_user)

                #Store Picture
                image_path =os.path.join(usr_images,fil)
                print 'Adding {}'.format(image_path)
                with open(image_path,'rb') as f:
                    new_user.picture.from_file(f, store = store)

def generateThumbnails( height = None, width = None ):
    with session_scope() as session:
        for usr in session.query( User ).all():
            if width:
                usr_thumb = usr.picture.generate_thumbnail(store=store,\
                                                            width = width)
            elif height:
                usr_thumb = usr.picture.generate_thumbnail(store=store, \
                                                            height = height)


if __name__ == '__main__':
    metadata.drop_all(engine)
    metadata.create_all(engine)
    print 'Storing Users'
    storeSomeUsers()
    generateThumbnails(width = 50)
