from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from .security.policy import SecurityPolicy
import random


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings) as config:
        session_factory = SignedCookieSessionFactory(settings['auth.secret'],
                                   secure=True,
                                   httponly=True)
        config.set_session_factory(session_factory)
        config.set_security_policy(SecurityPolicy(secret=settings['auth.secret']))
        config.set_default_permission("read")
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.include('.models')
        config.scan()
    return config.make_wsgi_app()
