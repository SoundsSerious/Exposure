# -*- coding: utf-8 -*-
"""
Created on Sun Nov 13 11:17:50 2016

@author: Sup
"""

from twisted.internet import reactor, threads
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.python import context
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import uuid
import functools

engine = create_engine(
    'sqlite:///test.sql',
    connect_args={'check_same_thread': False},
    echo=False)

session_factory = sessionmaker(bind=engine)
scopefunc = functools.partial(context.get, "uuid")
Session = scoped_session(session_factory, scopefunc=scopefunc)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)

Base.metadata.create_all(bind=engine)


class TestPage(Resource):
    isLeaf = True

    def render_GET(self, request):
        context.call({"uuid": str(uuid.uuid4())}, self._render, request)
        return NOT_DONE_YET

    def render_POST(self, request):
        return self.render_GET(request)

    def work_with_db(self):
        user = User(name="TestUser")
        Session.add(user)
        Session.commit()
        return user

    def _render(self, request):
        print "session: ", id(Session())
        d = threads.deferToThread(self.work_with_db)

        def success(result):
            html = "added user with name - %s" % result.name
            request.write(html.encode('UTF-8'))
            request.finish()
            Session.remove()
        call = functools.partial(context.call, {"uuid": scopefunc()}, success)
        d.addBoth(call)
        return d

if __name__ == "__main__":
    reactor.listenTCP(8888, Site(TestPage()))
    reactor.run()