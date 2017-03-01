"""Base classes handy for use with PB clients.
"""

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.spread import pb

from twisted.spread.pb import PBClientFactory
from twisted.internet import protocol, defer
from twisted.python import log
from twisted.cred.credentials import IAnonymous

class IEmailStorage(credentials.ICredentials):
    '''Check If Email Has Been Registered, If Not Register'''

    def checkEmails(email):
        '''where we check if emails are in EMAILS'''

@implementer(IEmailStorage)
class EmailAuth(object):

    def __init__(self, email):
        self.email = email.strip()

class ReconnectingPBClientFactory(PBClientFactory,
                                 protocol.ReconnectingClientFactory):
    """Reconnecting client factory for PB brokers.

    Like PBClientFactory, but if the connection fails or is lost, the factory
    will attempt to reconnect.

    Instead of using f.getRootObject (which gives a Deferred that can only
    be fired once), override the gotRootObject method.

    Instead of using the newcred f.login (which is also one-shot), call
    f.startLogin() with the credentials and client, and override the
    gotPerspective method.

    Instead of using the oldcred f.getPerspective (also one-shot), call
    f.startGettingPerspective() with the same arguments, and override
    gotPerspective.

    gotRootObject and gotPerspective will be called each time the object is
    received (once per successful connection attempt). You will probably want
    to use obj.notifyOnDisconnect to find out when the connection is lost.

    If an authorization error occurs, failedToGetPerspective() will be
    invoked.
    To use me, subclass, then hand an instance to a connector (like
    TCPClient).
    """

    def __init__(self):
       PBClientFactory.__init__(self)
       self._doingLogin = False
       self._doingGetPerspective = False

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed'
        PBClientFactory.clientConnectionFailed(self, connector, reason)
        # Twisted-1.3 erroneously abandons the connection on non-UserErrors.
        # To avoid this bug, don't upcall, and implement the correct version
        # of the method here.
        if self.continueTrying:
           print 'retrying...'
           self.connector = connector
           self.retry()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost'
        PBClientFactory.clientConnectionLost(self, connector, reason, reconnecting=True)
        RCF = protocol.ReconnectingClientFactory
        RCF.clientConnectionLost(self, connector, reason)

    def clientConnectionMade(self, broker):
        print 'connection made'
        self.resetDelay()
        PBClientFactory.clientConnectionMade(self, broker)
        if self._doingLogin:
            self.doLogin(self._root)
        if self._doingGetPerspective:
           self.doGetPerspective(self._root)
           self.gotRootObject(self._root)

    # oldcred methods
    def startGettingPerspective(self, username, password, serviceName, perspectiveName=None, client=None):
        self._doingGetPerspective = True
        if perspectiveName == None:
            perspectiveName = username
            self._oldcredArgs = (username, password, serviceName, perspectiveName, client)

    def doGetPerspective(self, root):
        #oldcred getPerspective()
        (username, password, serviceName, perspectiveName, client) = self._oldcredArgs
        d = self._cbAuthIdentity(root, username, password)
        d.addCallback(self._cbGetPerspective,
                       serviceName, perspectiveName, client)
        d.addCallbacks(self.gotPerspective, self.failedToGetPerspective)


    def _cbEmailLogin(self, root, credentials, client):
        return root.callRemote("loginEmail", credentials.email, client)

    # newcred methods
    def login(self, credentials, client=None):
        """
        Login and get perspective from remote PB server.

        Currently the following credentials are supported::

        L{twisted.cred.credentials.IUsernamePassword}
        L{twisted.cred.credentials.IAnonymous}

        @rtype: L{Deferred}
        @return: A L{Deferred} which will be called back with a
        L{RemoteReference} for the avatar logged in to, or which will
        errback if login fails.
        """
        d = self.getRootObject()

        if IAnonymous.providedBy(credentials):
            d.addCallback(self._cbLoginAnonymous, client)
        elif IEmailStorage.providedBy(credentials):
            d.addCallback(self._cbEmailLogin, credentials, client)
        else:
            d.addCallback(
                self._cbSendUsername, credentials.username,
                credentials.password, client)
        return d

    def failedToGetPerspective(self, why):
        """The login process failed, most likely because of an authorization
        failure (bad password), but it is also possible that we lost the new
        connection before we managed to send our credentials.
        """
        log.msg("ReconnectingPBClientFactory.failedToGetPerspective")
        if why.check(pb.PBConnectionLost):
            log.msg("we lost the brand-new connection")
            # retrying might help here, let clientConnectionLost decide
            return
        # probably authorization
        self.stopTrying() # logging in harder won't help
        log.err(why)

    def gotPerspective(self, perspective):
        """The remote avatar or perspective (obtained each time this factory
        connects) is now available."""
        print 'got {}'.format(perspective)

    def gotRootObject(self, root):
        """The remote root object (obtained each time this factory connects)
        is now available. This method will be called each time the connection
        is established and the object reference is retrieved."""
        print 'got {}'.format(root)


#   def startLogin(self, credentials, client=None):
#        self._credentials = credentials
#        self._client = client
#        d = defer.maybeDeferred(self.doLogin, self._root)
#        return d

#   def doLogin(self, root):
#        # newcred login()
#        d = self._cbSendUsername(root, self._credentials.username,
#                                 self._credentials.password, self._client)
#        d.addCallbacks(self.gotPerspective, self.failedToGetPerspective)
#        return d


#   # methods to override

#

#


#def getPerspective(self, *args):
#    raise RuntimeError, "getPerspective is one-shot: use startGettingPerspective instead"