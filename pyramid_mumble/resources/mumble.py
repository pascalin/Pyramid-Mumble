import pymumble_py3 as pymumble
from ..security import x509
from pyramid.httpexceptions import HTTPSeeOther, HTTPInsufficientStorage


class MumbleSessionFactory:
    connections = {}

    def __init__(self, request):
        if not request.is_authenticated:
            raise HTTPSeeOther(request.route_path("login"))

        user = request.identity
        if user.email in self.connections:
            self.mumble = self.connections[user.email]
        else:
            try:
                # cert, key = x509.get_user_cert_and_key(request.identity)
                cert, key = x509.generate_selfsigned_cert(request.identity)
            except TypeError:
                raise HTTPSeeOther(request.route_path("settings"))

            if self.get_active_connections() >= int(request.registry.settings['mumble.max_clients']):
                raise HTTPInsufficientStorage

            mumble = pymumble.Mumble(
                host=request.registry.settings['mumble.host'],
                user=user.username,
                password=request.registry.settings['mumble.password'],
                certfile=cert,
                keyfile=key,
                stereo=True,
                debug=request.registry.settings['mumble.debug'].lower() == 'true',
            )
            mumble.set_application_string("Pyramid-Mumble")
            # mumble.start()
            self.connections[user.email] = mumble
            self.mumble = mumble
            # self.mumble_user = mumble.users.myself

    def get_active_connections(self):
        return len([_ for _ in self.connections.values() if _.is_ready()])