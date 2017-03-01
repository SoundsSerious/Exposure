# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 18:40:18 2016

@author: Cabin
"""
import os,sys
import hashlib

from contextlib import contextmanager

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import sqlalchemy_imageattach
from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy_imageattach.context import store_context
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import case
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.types import Enum
from sqlalchemy.orm import *

from twisted.internet import defer, reactor, protocol, threads
from twisted.python import context

from geoalchemy2 import *
from geoalchemy2.shape import to_shape

from random import *
from datetime import datetime
import time
import traceback
import enum
import functools
import json

from config import *
from json_interface import *

path = EXP_PATH

engine = create_engine( ENG_STR )

metadata = MetaData(engine)
Base = declarative_base(metadata=metadata, cls = (JsonSerializableBase,))

scopefunc = functools.partial(context.get, "uuid")

session_factory  = sessionmaker(bind=engine)
Session = scoped_session(session_factory, scopefunc = scopefunc)

LAT,LONG = 26.7153, -80.053

print 'Storing images in {}'.format(STORE.path)
###############################################################################
#Twisted Interface
###############################################################################

class ITwistedData(object):
    '''In Which Social Database Interaction Occurs

    sqlalchemy_methods should not be run simultaniously... defer returning is problematic
    in recursive setting'''

    @staticmethod
    def sqlalchemy_method(function):

        @defer.inlineCallbacks
        def defferedThread(self,*args, **kwargs):
            # this function does some db work
            @ScopedSession(engine=engine)
            def process(session):
                # this method will be run in a thread and is passed a session by the decorator
                results = function(self,session,*args, **kwargs)
                return results
            # call the internal process function in a thread
            try:
                results = yield threads.deferToThread(process)
            except Exception as e:
                # do something with exceptions
                print 'ERROR: {}'.format(e)
                ex_type, ex, tb = sys.exc_info()
                traceback.print_tb(tb)
                results = None
            defer.returnValue(results)
        return defferedThread

class ScopedSession(object):
    SESSIONMAKER = None      # this is the single sessionmaker instance

    def __init__(self, engine, auto_commit=True):
        assert engine is not None, "Must pass a valid engine parameter"
        self._auto_commit = auto_commit
        if ScopedSession.SESSIONMAKER is None:
            ScopedSession.SESSIONMAKER = scoped_session(sessionmaker(expire_on_commit=True,\
                                                                     bind=engine))

    def __call__(self, func):
        #This is what gets called
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            db_session = ScopedSession.SESSIONMAKER()
            try:
                results = func(db_session, *args, **kwargs)
                db_session.commit()
                # should we rollback for safety?
                if not self._auto_commit:
                    db_session.rollback()
            except Exception as e:
                print 'ERROR: > rollback'
                print e
                db_session.rollback()
                raise
            finally:
                # release the session back to the connection pool
                print 'session close'
                db_session.close()
            return results
        return wrapper

try:
    from sqlalchemy import inspect
    from sqlalchemy.orm.state import InstanceState
except ImportError as e:
    def __nomodule(*args, **kwargs): raise e
    inspect = __nomodule
    InstanceState = __nomodule

###############################################################################
#User Model
###############################################################################
#Higher Levels Are Lower Use <
SECURITY_MODES = dict(
            #Staffs / Wizards
            super_user = -69,
            admin = -13,

            #Real MVPs
            owner = 0,

            #Users / Plebes
            authorized = 1,
            uninitalized = 2,
            new = 3,

            #Jerks
            kicked = 10)

friendship = Table(
    'user_friendship', Base.metadata,
    Column('friend_a_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('friend_b_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('created_date',DateTime, default=datetime.utcnow)
)

class User(Base):
    """User model. Call Properties From Within Session Scope"""
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    #Basic Information
    name = Column(Unicode, nullable=True)
    email = Column(String(255),nullable = False)
    info = Column( Text, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)

    #Modes
    user_mode = Column(Integer,default = SECURITY_MODES['new'])

    #References
    pictures = image_attachment('UserPicture', uselist = True)
    locations = relationship('UserSpot', back_populates = 'user', order_by="UserSpot.created")
    proj_owned = relationship('Project')
    staring_in = relationship("Role", back_populates="selected")

    @hybrid_property
    def current_location(self):
        '''Call From Session...Gets Last Location Added'''
        if self.locations:
            return self.locations[-1]

    @current_location.expression
    def current_location(cls):
        return select([UserSpot.id]).where(UserSpot.user_id == cls.id)\
                                    .order_by(desc(UserSpot.created))\
                                    .label('current_location')

    def checkUserAuthorized(self):
        return self.user_mode < SECURITY_MODES['uninitalized']

    @property
    def object_id(self):
        key = '{0}'.format(self.id)
        return int(hashlib.sha1(key).hexdigest(), 16)

    @property
    def user_json(self):
        '''should be called from within scope of session'''
        with store_context(STORE):
            pictures = list([pic.locate() for pic in self.pictures])
        if self.current_location:
            loc = self.current_location.latlong
        else:
            loc = None
        info = dict(name = self.name,\
                    info = self.info,\
                    location = loc,\
                    images = pictures,\
                    friends = list([f.id for f in self.all_friends])
                    )
        return json.dumps(info, ensure_ascii=False)



    # this relationship is used for persistence
    friends = relationship("User", secondary=friendship,
                           primaryjoin=id==friendship.c.friend_a_id,
                           secondaryjoin=id==friendship.c.friend_b_id,
    )

friendship_union = select([
                        friendship.c.friend_a_id,
                        friendship.c.friend_b_id
                        ]).union(
                            select([
                                friendship.c.friend_b_id,
                                friendship.c.friend_a_id]
                            )
                    ).alias()

User.all_friends = relationship('User',
                       secondary=friendship_union,
                       primaryjoin=User.id==friendship_union.c.friend_a_id,
                       secondaryjoin=User.id==friendship_union.c.friend_b_id,
                       viewonly=True)

class UserSpot(Base):
    """Basic Implementation Of Location"""
    __tablename__ = 'user_spot'
    id = Column(Integer, primary_key=True)
    user = relationship('User', back_populates = 'locations')
    user_id = Column(Integer, ForeignKey('user.id'))

    created = Column(DateTime, default=datetime.now())
    geom = Column(Geometry(geometry_type='POINT', srid=-1),\
        default = 'POINT({:3.9f} {:3.9f})'.format(LAT,LONG))

    @property
    def latlong(self):
        pt = to_shape(self.geom)
        return pt.x, pt.y

    @property
    def pt_txt(self):
        pt = to_shape(self.geom)
        pt_txt = 'POINT({} {})'.format(pt.x, pt.y)
        return pt_txt

    @property
    def object_id(self):
        key = '{0},{1}'.format(self.project_id, self.order_index)
        return int(hashlib.sha1(key).hexdigest(), 16)

class UserPicture(Base, Image):
    """User picture model."""
    __tablename__ = 'user_picture'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    user = relationship('User')
    order_index = Column(Integer,primary_key = True)
    created_date = Column(DateTime, default=datetime.utcnow)

    @property
    def object_id(self):
        return int(hashlib.sha1(str(self.user_id)).hexdigest(), 16)

###############################################################################
#Project Model
###############################################################################

membership = Table(
    'project_membership', Base.metadata,
    Column('project_id', Integer, ForeignKey('project.id'), primary_key=True),
    Column('member_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('created_date',DateTime, default=datetime.utcnow)
)

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer,primary_key = True)
    name = Column(Unicode, nullable=False)
    info = Column( Text, nullable=True)
    owner_id = Column(Integer,ForeignKey('user.id'))
    created_date = Column(DateTime, default=datetime.utcnow)


    pictures = image_attachment('ProjectImage', uselist = True)
    locations = relationship('ProjectSpot',uselist = True)
    roles = relationship('Role',uselist = True)

    @property
    def project_json(self):
        '''should be called from within scope of session'''
        with store_context(STORE):
            pictures = list([pic.locate() for pic in self.pictures])
        if self.current_location:
            loc = self.current_location.latlong
        else:
            loc = None
        info = dict(name = self.name,
                    info = self.info,
                    location = loc,
                    images = pictures,
                    members = list([m.id for m in self.all_members]),
                    roles = list([r.id for r in self.roles])
                    )
        return json.dumps(info, ensure_ascii=False)

    @property
    def current_location(self):
        if self.locations:
            return self.locations[-1]
    #members = relationship('User',  secondary = membership,\
    #                                backref =   backref('project_membership',lazy='dynamic'))

    # this relationship is used for persistence
    members = relationship("User", secondary=membership,
                           primaryjoin = id==membership.c.project_id,
                           secondaryjoin=User.id==membership.c.member_id)

member_union = select([
                        membership.c.project_id,
                        membership.c.member_id
                        ]).union(
                            select([
                                membership.c.project_id,
                                membership.c.member_id]
                            )
                    ).alias()

Project.all_members = relationship('User',
                       secondary=member_union,
                       primaryjoin=Project.id==member_union.c.project_id,
                       secondaryjoin=User.id==member_union.c.member_id,
                       viewonly=True)

class ProjectImage(Base, Image):
    """User picture model."""
    __tablename__ = 'project_pictures'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    project = relationship(Project)
    order_index = Column(Integer,primary_key = True)
    created_date = Column(DateTime, default=datetime.utcnow)

    @property
    def object_id(self):
        key = '{0},{1}'.format(self.project_id, self.order_index)
        return int(hashlib.sha1(key).hexdigest(), 16)

class ProjectSpot(Base):
    """Basic Implementation Of Location"""
    __tablename__ = 'project_spot'
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.now())
    geom = Column(Geometry(geometry_type='POINT', srid=-1))

    project = relationship('Project', back_populates = 'locations')
    parent_id = Column(Integer, ForeignKey('project.id'),nullable=True)

    created_date = Column(DateTime, default=datetime.utcnow)

    @property
    def latlong(self):
        pt = to_shape(self.geom)
        return pt.x, pt.y

    @property
    def pt_txt(self):
        pt = to_shape(self.geom)
        pt_txt = 'POINT({} {})'.format(pt.x, pt.y)
        return pt_txt
###############################################################################
#Roles Class
###############################################################################
ROLE_MODES = dict( new = 0, casting = 1, auditioning = 2, selected = 3, archived = 4)

role_invites = Table(
    'role_invites', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('invited_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('created_date',DateTime, default=datetime.utcnow)
)

role_auditioning = Table(
    'role_auditioning', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('actor_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('created_date',DateTime, default=datetime.utcnow)
)

class Role(Base):
    """Roles define the relationship between users and projects"""
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    character_name = Column(String(255),nullable = False)
    info = Column(Text,nullable = True)

    #Modes
    role_status = Column(Integer,default = ROLE_MODES['new'])

    #Relationships
    project_id = Column(Integer, ForeignKey('project.id'),nullable=True)
    pictures = image_attachment('RoleImage', uselist = True)

    #Auditioning Cast List Relationships (Invite, Audition, Select Pipeline)
    selected_id = Column(Integer, ForeignKey('user.id'))
    selected = relationship("User", back_populates="staring_in")
    
    # this relationship is used for persistence
    invitees = relationship("User", secondary=role_invites,
                           primaryjoin = id==role_invites.c.role_id,
                           secondaryjoin=User.id==role_invites.c.invited_id,
    )
    
    auditioners = relationship("User", secondary=role_auditioning,
                           primaryjoin = id==role_auditioning.c.role_id,
                           secondaryjoin=User.id==role_auditioning.c.actor_id,
    )

invite_union = select([
                        role_invites.c.role_id,
                        role_invites.c.invited_id
                        ]).union(
                            select([
                                role_invites.c.invited_id,
                                role_invites.c.role_id]
                            )
                    ).alias()

audition_union = select([
                        role_auditioning.c.role_id,
                        role_auditioning.c.actor_id
                        ]).union(
                            select([
                                role_auditioning.c.actor_id,
                                role_auditioning.c.role_id]
                            )
                    ).alias()                            
                            
#List Of Primary Keys To Users In Role
Role.invites = relationship('User',
                       secondary=invite_union,
                       primaryjoin=Role.id==invite_union.c.role_id,
                       secondaryjoin=User.id==invite_union.c.invited_id,
                       viewonly=True)

Role.auditions = relationship('User',
                       secondary=audition_union,
                       primaryjoin=Role.id==audition_union.c.role_id,
                       secondaryjoin=User.id==audition_union.c.actor_id,
                       viewonly=True)


class RoleImage(Base, Image):
    """User picture model."""
    __tablename__ = 'role_pictures'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    role = relationship(Role)
    order_index = Column(Integer,primary_key = True)
    created_date = Column(DateTime, default=datetime.utcnow)

    @property
    def object_id(self):
        key = '{0},{1}'.format(self.role_id, self.order_index)
        return int(hashlib.sha1(key).hexdigest(), 16)

###############################################################################
#Dummy Data Loading
###############################################################################

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


def threaded(fn):
    @functools.wraps(fn)  # functools.wraps
    def wrapper(*args, **kwargs):
        return threads.deferToThread(fn, *args, **kwargs)  # t.i.threads.deferToThread
    return wrapper

import random
from glob import glob

LORN_IPSUM = '''Lorem ipsum dolor sit amet, ut altera adipiscing reformidans his. Ut suas clita epicuri eos. Justo verterem eu pri, autem iudicabit in mea. Id vel alienum fabellas definitionem, ex usu putant corpora copiosae, nam aliquip posidonium no.'''*9

LAT,LONG = 26.7153, -80.053

PRJ_DIR = os.path.join( EXP_PATH, 'project_images')
PRJ_IMAGE = glob(PRJ_DIR+'/*.jpg')
PROJECTS = [os.path.basename(prj).replace('.jpg','').replace('.',' ') \
                                    for prj in PRJ_IMAGE]
PRJ_LOC = [(LONG+(random.random()-0.5)*0.1,LONG+(random.random()-0.5)*0.1)for prj in PROJECTS]  
             
USR_DIR = os.path.join( EXP_PATH, 'user_images')
USR_IMAGE = glob(USR_DIR+'/*.jpg')
USERS = [os.path.basename(prj).replace('.jpg','').replace('.',' ') \
                                    for prj in USR_IMAGE]
N = len(USERS)
USR_LOC = [(LAT+(random.random()-0.5)*0.1,LONG+(random.random()-0.5)*0.1) for prj in USERS]

PRJ_MEMBERS = {prj: list(set([random.choice(USERS) for i in range(random.randint(1,N-3))])) \
                                              for prj in PROJECTS}
                                                  
def makeProjects():
    with session_scope() as session:
        for i,(proj) in enumerate(PROJECTS):
            actors =  PRJ_MEMBERS[proj]
            #Create Project
            firstActor = '{}@gmail.com'.format(actors[0].replace(' ','.'))
            firstUser = session.query(User).filter(User.email == firstActor).first()
            project = Project(name = proj, info = LORN_IPSUM, owner_id = firstUser.id )
            session.add(project)
            
            #Add Members
            for actor in actors:
                email = '{}@gmail.com'.format(actor.replace(' ','.'))
                q = session.query(User).filter(User.email == email)
                member = q.first()
                project.members.append(member)

                #add role
                role = Role(character_name=member.name, info = LORN_IPSUM)
                project.roles.append(role)

            #Add The Geolocationary Data
            geo = ProjectSpot(geom = 'POINT({:3.3f} {:3.3f})'.format(LAT+(random.random()-0.5)*0.1,\
                                                                      LONG+(random.random()-0.5)*0.1),\
                parent_id = None)
            session.add(geo)

            project.locations.append(geo)
            session.merge(project)

            #Add Some Pictures
            path = PRJ_IMAGE[i]
            picture = project.pictures.get_image_set(order_index = i+1)
            with open(path,'rb') as f:
                picture.from_file(f, store=STORE)


def makeFriends():
    with session_scope() as session:
        user_count = session.query(User).count()
        all_users = session.query(User).all()
        for user in all_users:
            friends = sample( all_users, randint(0,min(randint(0,5),len(all_users))))
            user.friends = friends



def storeSomeUsers():

    with session_scope() as session:
        print 'Storing Users'
        for fil in os.listdir(USR_IMG):
            if '.jpg' in fil:
                print 'Adding {}'.format(fil.replace('.jpg','').replace('.',' '))

                name = fil.replace('.jpg','').replace('.',' ')
                email = fil.replace('.jpg','') + '@gmail.com'



                new_user = User(name = name, email = email, info= LORN_IPSUM,\
                                user_mode = SECURITY_MODES['authorized'])
                geo = UserSpot( geom = 'POINT({:3.3f} {:3.3f})'.format(LAT+random.random()-0.5,\
                                                            LONG+random.random()-0.5),
                                created = datetime.now())
                time.sleep(0.1)
                geo2 = UserSpot( geom = 'POINT({:3.3f} {:3.3f})'.format(LAT+random.random()-0.5,\
                                                            LONG+random.random()-0.5),
                                 created = datetime.now())
                new_user.locations.append(geo)
                new_user.locations.append(geo2)
                #Add Data After Established Refs
                session.add(geo)
                session.add(geo2)
                session.add(new_user)

                #Store Picture
                image_path =os.path.join(USR_IMG,fil)
                print 'Adding {}'.format(image_path)
                profile_pic = new_user.pictures.get_image_set(order_index = 1)
                with open(image_path,'rb') as f:
                    profile_pic.from_file(f, store = STORE)


def generateThumbnails( height = None, width = None, ratio = None):
    with session_scope() as session:
        for usr in session.query( User ).all():
            for image_set in usr.pictures.image_sets:
                if width:
                    usr_thumb = image_set.generate_thumbnail(store=STORE,\
                                                                width = width)
                elif height:
                    usr_thumb = image_set.generate_thumbnail(store=STORE, \
                                                                height = height)
                elif ratio:
                    usr_thumb = image_set.generate_thumbnail(store=STORE, \
                                                                ratio = ratio)




if __name__ == '__main__':
    metadata.drop_all(engine)
    metadata.create_all(engine)
    storeSomeUsers()
    generateThumbnails(width = 200)
    generateThumbnails(ratio = 1)
    makeProjects()
    makeFriends()



