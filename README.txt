Pyramid Mumble
==============

Pyramid web interface to Murmur and Mumble.

It assumes that you have a working Murmur (Mumble server) instance, whose details you need to enter into the .ini
configuration file. As an alternative, you can simply configure a Mumble-web interface and link it from the profile
view by entering the required information in the .ini file.

Getting Started
---------------

- Change directory into your newly created project if not already there. Your
  current directory should be the same as this README.txt file and setup.py.

    cd Pyramid-Mumble

- Create a Python virtual environment, if not already created.

    python3 -m venv env

- Upgrade packaging tools, if necessary.

    env/bin/pip install --upgrade pip setuptools

- Install the project in editable mode with its testing requirements.

    env/bin/pip install -e ".[testing]"

- Initialize and upgrade the database using Alembic.

    - Generate your first revision.

        env/bin/alembic -c development.ini revision --autogenerate -m "init"

    - Upgrade to that revision.

        env/bin/alembic -c development.ini upgrade head

- Load default data into the database using a script.

    env/bin/initialize_pyramid_mumble_db development.ini

- Run your project's tests.

    env/bin/pytest

- Run your project.

    env/bin/pserve development.ini

In order to enable the websocket part, you will need to use both gunicorn and eventlet:

`env/bin/gunicorn --paste production.ini -b 127.0.0.1:8000 --chdir YOUR_PYRAMID_MUMBLE_PATH -k eventlet -w 1`

ToDo
----

- The project is still in an early phase, but it can already self-generate x509 certificates to identify users, or they
can be uploaded and used to establish the Mumble connection. But the registration and access control to the Murmur server
still has to be implemented either using pymumble o even better ICE protocol (I already have an ICE mockup, but need to
include it).

- Sound is already being transmitted from the browser to Mumble but with a lot of jitter, so I figure that the rate of
transfer or something like that need to be modulated for this to work.

- Sound from pymumble to the browser is not implemented, but it should be very easy if one looks into the
 websocket to mumble part.
