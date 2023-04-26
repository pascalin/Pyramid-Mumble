from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from .security.policy import SecurityPolicy
import socketio


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    sio_server = socketio.Server(logger=True, engineio_logger=True, namespaces=['/', '/audio'])

    global thread
    thread = None

    def background_thread():
        """Example of how to send server generated events to clients."""
        count = 0
        while True:
            sio_server.sleep(30)
            count += 1
            sio_server.emit('my_response', {'data': 'Server generated event #{}'.format(count)})

    if thread is None:
        # thread = sio_server.start_background_task(background_thread)
        # ToDo: it is necessary to end this thread when Pyramid stops or gets killed.
        pass

    def sio(request):
        return sio_server

    with Configurator(settings=settings) as config:
        session_factory = SignedCookieSessionFactory(settings['auth.secret'],
                                   secure=True,
                                   httponly=True)
        config.set_session_factory(session_factory)
        config.set_security_policy(SecurityPolicy(secret=settings['auth.secret']))
        config.add_request_method(sio, reify=True)
        config.set_default_permission("read")
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.include('.models')
        config.scan()
    pyramid_app = config.make_wsgi_app()
    return socketio.WSGIApp(sio_server, pyramid_app)
