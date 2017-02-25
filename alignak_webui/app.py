#!/usr/bin/python
# -*- coding: utf-8 -*-

# Else pylint alerts on declared global variables
# pylint: disable=invalid-name

# Copyright (c) 2015-2017:
#   Frederic Mohier, frederic.mohier@alignak.net
#
# This file is part of (WebUI).
#
# (WebUI) is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# (WebUI) is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with (WebUI).  If not, see <http://www.gnu.org/licenses/>.

"""
Usage:
    {command} [-h] [-v] [-d] [-b=url] [-n=hostname] [-p=port] [<cfg_file>...]

Options:
    -h, --help                  Show this screen.
    -v, --version               Show application version.
    -b, --backend url           Specify backend URL
    -n, --hostname host         Specify WebUI host (or ip address)
    -p, --port port             Specify WebUI port
    -d, --debug                 Run in debug mode (more info to display) [default: False]

Use cases:
    Display help message:
        {command} -h
    Display current version:
        {command} -v

    Run application in default mode:
        {command}

    Run application in default mode and specify a configuration file:
        {command} /etc/ui-settings.cfg

    Run application and specify the backend URL:
        {command} -b=backend

    Run application in debug mode and listen on all interfaces:
        {command} -d -b=backend -n=0.0.0.0 -p=5001

    Exit code:
        0 if all is ok
        1 configuration error
        2 run error
        64 if command line parameters are not used correctly
        99 application started but server not run (test application start)

"""

from __future__ import print_function

import os
import time
import json
import logging
import threading

# Bottle Web framework
import bottle
from bottle import run, redirect, request, response, static_file
from bottle import template, BaseTemplate, TEMPLATE_PATH
from bottle import RouteBuildError, parse_auth

# Session management
from beaker.middleware import SessionMiddleware

# Command line interpreter
from docopt import docopt, DocoptExit

# Application import
from alignak_webui import __manifest__, set_app_config
from alignak_webui.utils.logger import setup_logging
from alignak_webui.utils.locales import init_localization
from alignak_webui.backend.backend import BackendException
from alignak_webui.backend.datamanager import DataManager
from alignak_webui.webui import WebUI

app = application = bottle.Bottle()

# -----
# Test mode for the application
# -----
if os.environ.get('ALIGNAK_WEBUI_TEST'):
    print("Application is in test mode")
else:
    print("Application is in production mode")

# pylint: disable=redefined-variable-type
args = {}
if __name__ == '__main__':
    try:
        print("Parsing command line arguments")
        args = docopt(__doc__, version=__manifest__['version'])
    except DocoptExit as exp:
        print("Command line parsing error: \n%s" % exp)
        exit(64)

# -----
# Application configuration file
# -----
app_name = __manifest__['name'].lower()
# Search for configuration files in several locations
cfg_filenames = [
    '/usr/local/etc/%s/settings.cfg' % app_name,
    '/etc/%s/settings.cfg' % app_name,
    '~/%s/settings.cfg' % app_name,
    os.path.abspath('../etc/settings.cfg'),
    os.path.abspath('./etc/settings.cfg'),
    os.path.abspath('./settings.cfg'),
]
# Configuration file name in environment
if os.environ.get('ALIGNAK_WEBUI_CONFIGURATION_FILE'):
    cfg_filenames = [os.environ.get('ALIGNAK_WEBUI_CONFIGURATION_FILE')]
    print("Application configuration file name from environment: %s" % cfg_filenames)
# Configuration file name in command line parameters
if '<cfg_file>' in args and args['<cfg_file>']:
    cfg_filenames = args['<cfg_file>']
    print("Application configuration file name from command line: %s" % cfg_filenames)


app_configuration_file = None
for cfg_filename in cfg_filenames:
    if os.path.isfile(cfg_filename):
        app.config.load_config(cfg_filename)
        print("Configuration read from: %s" % cfg_filename)
        app_configuration_file = cfg_filename
        break
else:
    print("***** Application configuration file not found.")
    print("***** Searched in: %s" % cfg_filenames)
    exit(1)

# -----
# Check application configuration file change
# -----
if os.environ.get('ALIGNAK_WEBUI_CONFIGURATION_THREAD'):
    def check_config(_app, filename, interval=5):
        """Thread to check if configuration file changed"""
        print("Thread for checking configuration file change, file: %s" % filename)
        modification_time = os.path.getmtime(filename)
        while True:
            time.sleep(interval)
            print("Checking configuration file change...")
            if modification_time < os.path.getmtime(filename):
                print("Application configuration file changed, reloading configuration...")
                modification_time = os.path.getmtime(filename)
                _app.config.load_config(filename)
    cfg_check_thread = threading.Thread(target=check_config,
                                        name='application_configuration_check',
                                        args=(app, app_configuration_file, 10))
    cfg_check_thread.daemon = True
    cfg_check_thread.start()

# -----
# Debug and test mode
# -----
if os.environ.get('BOTTLE_DEBUG'):
    app.config['bottle.debug'] = True
    print("Bottle is in debug mode from environment")

if os.environ.get('ALIGNAK_WEBUI_DEBUG'):
    app.config['%s.debug' % app_name] = True
    print("Application is in debug mode from environment")

if '--debug' in args and args['--debug']:
    app.config['bottle.debug'] = True
    app.config['%s.debug' % app_name] = True
    print("Application is in debug mode from command line")

# -----
# Application backend
# -----
if os.environ.get('ALIGNAK_WEBUI_BACKEND'):
    app.config['%s.alignak_backend' % app_name] = os.environ.get('ALIGNAK_WEBUI_BACKEND')
    print("Application backend from environment: %s" % os.environ.get('ALIGNAK_WEBUI_BACKEND'))
if '--backend' in args and args['--backend']:
    app.config['%s.alignak_backend' % app_name] = args['--backend']
    print("Application backend from command line: %s" % args['--backend'])

print("Application backend: %s" % app.config.get('%s.alignak_backend' % app_name,
                                                 'http://127.0.0.1:5000'))

if '--host' in args and args['--host']:
    app.config['host'] = args['--host']
    print("Listening interface from command line: %s" % app.config.get('host', '127.0.0.1'))

if '--port' in args and args['--port']:
    app.config['port'] = args['--port']
    print("Listening port from command line: %s" % app.config.get('port', '5001'))

# -----
# Application log
# -----
# Set application log level (default is INFO
log_level = 'INFO'
if app.config.get('%s.debug' % app_name, False):  # pragma: no cover - not testable easily...
    print("-> Activated DEBUG log")
    log_level = 'DEBUG'

log_filenames = [
    '/usr/local/etc/%s/logging.json' % app_name,
    '/etc/%s/logging.json' % app_name,
    '~/%s/logging.json' % app_name,
    os.path.abspath('../etc/logging.json'),
    os.path.abspath('./etc/logging.json'),
    os.path.abspath('./logging.json'),
]
if os.environ.get('ALIGNAK_WEBUI_LOGGER_FILE'):
    log_filenames = [os.environ.get('ALIGNAK_WEBUI_LOGGER_FILE')]
    print("Application logger configuration file from environment: %s"
          % os.environ.get('ALIGNAK_WEBUI_LOGGER_FILE'))

app_logger_file = None
logger = None
for log_filename in log_filenames:
    if setup_logging(log_filename):
        logger = logging.getLogger(app_name)
        logger.setLevel(log_level)
        print("Application logger configured from: %s" % log_filename)
        break
else:
    print("***** Application logger configuration file not found.")
    print("***** Searched in: %s" % log_filenames)
    exit(2)

logger.info("--------------------------------------------------------------------------------")
logger.info("%s, version %s", __manifest__['name'], __manifest__['version'])
logger.info("Copyright %s", __manifest__['copyright'])
logger.info("License: %s", __manifest__['license'])
logger.info("--------------------------------------------------------------------------------")
logger.info("Doc: %s", __manifest__['doc'])
logger.info("Release notes: %s", __manifest__['release'])
logger.info("--------------------------------------------------------------------------------")

logger.info("--------------------------------------------------------------------------------")
logger.info("listening on %s:%d (debug mode: %s)",
            app.config.get('host', '127.0.0.1'),
            int(app.config.get('port', '5001')),
            app.config.get('debug', False))
logger.info("using Alignak Backend on %s",
            app.config.get('%s.alignak_backend' % app_name, 'http://127.0.0.1:5000'))
logger.info("--------------------------------------------------------------------------------")

logger.debug("Application settings: ")
# Make the 'application.key' also available as 'key'
add_to_config = {}
for key, value in sorted(app.config.items()):
    if key.startswith(app_name):
        add_to_config[key.replace(app_name + '.', '')] = value
    logger.debug(" %s = %s", key, value)
logger.debug("--------------------------------------------------------------------------------")
logger.debug("Webui settings: ")
for key, value in add_to_config.items():
    app.config[key] = value
    logger.debug(" %s = %s", key, value)
logger.debug("--------------------------------------------------------------------------------")

# -----
# Application localization
# -----
_ = init_localization(app)
# Update configuration with translation method to use
app.config['_'] = _
# Provide translation methods to templates
BaseTemplate.defaults['_'] = _
print(_("Language is English (default)..."))

# -----
# Application extension
# -----
webapp = WebUI(app, name=app_name, config=app.config)
BaseTemplate.defaults['webui'] = webapp
app.config['webui'] = webapp

# -----
# Gloval application configuration
# -----
set_app_config(app.config)


# -----
# Application static files
# -----
@app.route('/static/<filename:path>')
def static(filename):
    """
    Main application static files
    Plugins declare their own static routes under /plugins
    """
    if not filename.startswith('plugins'):
        return static_file(
            filename, root=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
        )
    else:
        return static_file(
            filename, root=os.path.abspath(os.path.dirname(__file__))
        )


# -----
# Application modal windows
# -----
@app.route('/modal/<modal_name>')
def give_modal(modal_name):
    """
    Return template for a modal window
    """
    logger.debug("get modal window named: %s", modal_name)
    return template('modal_' + modal_name)


# --------------------------------------------------------------------------------------------------
# WebUI hooks
# --------------------------------------------------------------------------------------------------
@app.hook('config')
def on_config_change(_key, _value):
    """Hook called if configuration dictionary changed"""
    logger.warning("application configuration changed, key: %s = %s", _key, _value)
    if _key.startswith(app_name):
        app.config[_key.replace(app_name + '.', '')] = _value
        logger.warning("application configuration changed, *** key: %s = %s",
                       _key.replace(app_name + '.', ''), _value)


@app.hook('before_request')
def before_request():
    # pylint: disable=unsupported-membership-test, unsubscriptable-object
    """
    Function called since an HTTP request is received, and before any other function.

    Checks if a user session exists

    Some URLs do not need any authentication:
        - ping, heartbeat mechanism used for page or page elements refresh
        - login / logout
        - static files (js, css, ...)
    """
    logger.debug("before_request, url: %s", request.urlparts.path)

    # Static application and plugins files
    if request.urlparts.path.startswith('/static'):
        return

    # External URLs routing ...
    if request.urlparts.path.startswith('/external'):
        return

    # Get the server session (if it exists ...)
    session = request.environ['beaker.session']

    if 'edition_mode' in session:
        # Make session edition mode available in the templates
        BaseTemplate.defaults['edition_mode'] = session['edition_mode']
    else:
        session['edition_mode'] = False

    if 'current_user' in session:
        # Make session current user available in the templates
        BaseTemplate.defaults['current_user'] = session['current_user']

    # Public URLs routing ...
    if request.urlparts.path == '/ping' or \
       request.urlparts.path == '/heartbeat':
        return

    # Login/logout URLs routing ...
    if request.urlparts.path == '/login' or \
       request.urlparts.path == '/logout':
        return

    # Session authentication ...
    if 'current_user' not in session:
        # Redirect to application login page
        logger.warning(
            "The session expired or there is no user in the session."
            " Redirecting to the login page..."
        )

        # Stop Alignak backend thread
        # *****

        redirect('/login')

    # Get the WebUI instance
    webui = request.app.config['webui']

    current_user = session['current_user']
    if not webui.user_authentication(current_user.token, None):
        # Redirect to application login page
        logger.warning(
            "user in the session is not authenticated."
            " Redirecting to the login page..."
        )
        redirect('/login')

    # Make session current user available in the templates
    BaseTemplate.defaults['current_user'] = session['current_user']
    # Make session edition mode available in the templates
    BaseTemplate.defaults['edition_mode'] = session['edition_mode']
    # Initialize data manager and make it available in the request and in the templates
    if webui.datamgr is None:
        webui.datamgr = DataManager(
            backend_endpoint=request.app.config.get('%s.alignak_backend' % webui.name,
                                                    'http://127.0.0.1:5000'),
            session=request.environ['beaker.session']
        )
    request.app.datamgr = webui.datamgr
    # # Load initial objects from the DM
    # request.app.datamgr.load()
    BaseTemplate.defaults['datamgr'] = request.app.datamgr

    # logger.debug("before_request, call function for route: %s", request.urlparts.path)


# --------------------------------------------------------------------------------------------------
# Home page and login
# --------------------------------------------------------------------------------------------------
@app.route('/', 'GET')
def home_page():
    """
    Display home page -> redirect to /Dashboard
    """
    try:
        redirect(request.app.get_url('Livestate'))
    except RouteBuildError:
        return "No home page available in the application routes!"


@app.route('/login', 'GET')
def user_login():
    """
    Display user login page
    """
    session = request.environ['beaker.session']
    message = None
    if 'login_message' in session and session['login_message']:
        message = session['login_message']
        session['login_message'] = None
        logger.warning("login page with error message: %s", message)

    # Send login form
    return template(
        'login', {
            'login_text': request.app.config.get(
                'login_text', _('Welcome!<br> Log-in to use the application')
            ),
            'app_logo': request.app.config.get(
                'app_logo', '/static/images/alignak_white_logo.png'
            ),
            'message': message
        }
    )


@app.route('/logout', 'GET')
def user_logout():
    """
    Log-out the current logged-in user

    Clear and delete the user session
    """
    # Store user information in the server session
    session = request.environ['beaker.session']
    session.delete()

    # Log-out from application
    logger.info("Logout for current user")

    redirect('/login')


def check_backend_connection(_app, token=None, interval=10):
    """Thread to check if backend connection is alive"""
    print("Thread for checking backend connection is alive with %s" % app.config['alignak_backend'])

    backend = _app.datamgr.backend
    object_type = 'user'
    params = {}
    while True:
        time.sleep(interval)
        if not token:
            continue
        print("Checking backend connection...")
        try:
            result = backend.get(object_type, params=params, all_elements=False)
            logger.debug("check_backend_connection, found: %s: %s", object_type, result)
        except BackendException as exp:  # pragma: no cover, simple protection
            logger.exception("object_type, exception: %s", exp)
            raise ValueError(
                '%s, search: %s was not found in the backend' % (object_type, params)
            )


@app.route('/login', 'POST')
def user_auth():
    """
    Receive user login parameters (username / password) to authenticate a user

    Allowed authentication:
    - username/password from a login form
    - token and empty password
    """
    username = request.forms.get('username', None)
    password = request.forms.get('password', None)
    logger.info("login, user '%s' is signing in ...", username)

    session = request.environ['beaker.session']
    session['login_message'] = None
    if not webapp.user_authentication(username, password):
        # Redirect to application login page with an error message
        if 'login_message' not in session:
            session['login_message'] = _("Invalid username or password")
        logger.warning("user '%s' access denied, message: %s", username, session['login_message'])
        redirect('/login')

    logger.info("user '%s' (%s) signed in", username, session['current_user'].name)

    # -----
    # Start Alignak backend thread
    # -----
    # pylint: disable=fixme
    # TODO: run backend connection check thread
    # cfg_backend_thread = threading.Thread(target=check_backend_connection,
    #                                       name='backend_connection_check',
    #                                       args=(app, session['current_user'].token, 10))
    # cfg_backend_thread.daemon = True
    # cfg_backend_thread.start()

    redirect('/')


# --------------------------------------------------------------------------------------------------
# Ping / heartbeat
# --------------------------------------------------------------------------------------------------
@app.route('/heartbeat')
def heartbeat():
    """
    Application heartbeat
    """
    # Session authentication ...
    session = request.environ['beaker.session']
    if not session:
        response.status = 401
        response.content_type = 'application/json'
        return json.dumps({'status': 'ok', 'message': 'Session expired'})

    if 'current_user' not in session or not session['current_user']:
        response.status = 401
        response.content_type = 'application/json'
        return json.dumps({'status': 'ok', 'message': 'Session expired'})

    response.status = 200
    response.content_type = 'application/json'
    return json.dumps({'status': 'ok',
                       'message': "Current logged-in user: %s"
                                  % session['current_user'].get_username()})


@app.route('/ping')
def ping():
    # pylint: disable=too-many-return-statements
    """
    Request on /ping is a simple check alive that returns an information if UI refresh is needed

    If no session exists, it will always return 'pong' to inform that server is alive.

    Else:
        - if UI refresh is needed, requires the UI client to refresh
        - if action parameter is 'refresh', returns the required template view
        - if action parameter is 'done', the UI client did refresh the interface.

    Used by the header refresh to update the hosts/services states.
    """
    session = request.environ['beaker.session']
    if not session:
        response.status = 401
        response.content_type = 'application/json'
        return json.dumps({'status': 'ok', 'message': 'Session expired'})

    action = request.query.get('action', None)
    if action == 'done':
        # Acknowledge UI refresh
        session['refresh_required'] = False
        logger.debug("ping, refresh: %s", session['refresh_required'])
    elif action == 'refresh':
        page_template = request.query.get('template', None)
        if page_template:
            # Send rendered template
            return template(page_template)

        # pragma: no cover - should not happen
        response.status = 200
        response.content_type = 'application/json'
        return json.dumps({'status': 'ok',
                           'message': 'missing template name. '
                                      'Use /ping?action=refresh&template=name.'})
    elif action:
        response.status = 204
        response.content_type = 'application/json'
        return json.dumps({'status': 'ok',
                           'message': 'Unknown ping action parameter: %s' % action})

    # Check new data in the data manager for the page refresh
    session = request.environ['beaker.session']
    if 'refresh_required' in session and session['refresh_required']:
        # Require UI refresh
        response.status = 200
        response.content_type = 'application/json'
        return json.dumps({'status': 'ok', 'message': 'refresh'})

    response.status = 200
    response.content_type = 'application/json'
    return json.dumps({'status': 'ok', 'message': 'pong'})


# --------------------------------------------------------------------------------------------------
# WebUI routes
# --------------------------------------------------------------------------------------------------
# CORS decorator
def enable_cors(fn):
    """
    CORS decorator

    Send the CORS headers for ajax request
    """
    def _enable_cors(*_args, **_kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = \
            request.app.config.get('cors_acao', 'http://127.0.0.1')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = \
            'Origin, Accept, Authorization, X-HTTP-Method-Override, If-Match, Content-Type'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*_args, **_kwargs)

        # response.status = 204

    return _enable_cors


@app.route('/external/<widget_type>/<identifier>/<action:path>', method=['GET', 'POST', 'OPTIONS'])
@app.route('/external/<widget_type>/<identifier>', method=['GET', 'POST', 'OPTIONS'])
@enable_cors
def external(widget_type, identifier, action=None):
    # pylint: disable=too-many-return-statements, unsupported-membership-test
    # pylint: disable=unsubscriptable-object
    """
    Application external identifier

    Use internal authentication (if a user is logged-in) or external basic authentication provided
    by the requiring application.

    Search in the known 'widget_type' (widget or table) to find the element 'identifier'.

    Use the 'links' parameter to prefix the navigation URLs.
    """

    logger.info("external...")
    # Get the WebUI instance
    webui = request.app.config['webui']

    session = request.environ['beaker.session']
    if 'current_user' in session:
        current_user = session['current_user']

        if not webui.user_authentication(current_user.token, None):
            # Redirect to application login page
            logger.warning("user in the session is not authenticated. "
                           "Redirecting to the login page...")
            redirect('/login')
        credentials = current_user.token + ':'

    else:
        # Authenticate external access...
        if 'Authorization' not in request.headers or not request.headers['Authorization']:
            logger.warning("external application access denied")
            response.status = 401
            response.content_type = 'text/html'
            return _(
                '<div>'
                '<h1>External access denied.</h1>'
                '<p>To embed an Alignak WebUI widget or table, you must provide credentials.<br>'
                'Log into the Alignak WebUI with your credentials, or make a request '
                'with a Basic-Authentication allowing access to Alignak backend.</p>'
                '</div>'
            )

        # Get HTTP authentication
        authentication = request.headers.get('Authorization')
        username, password = parse_auth(authentication)

        if not webui.user_authentication(username, password):
            logger.warning("external application access denied for %s", username)
            response.status = 401
            response.content_type = 'text/html'
            return _(
                '<div>'
                '<h1>External access denied.</h1>'
                '<p>The provided credentials do not grant you access to Alignak WebUI.<br>'
                'Please provide proper credentials.</p>'
                '</div>'
            )

        current_user = session['current_user']
        credentials = current_user.token + ':'

        # Make session data available in the templates
        BaseTemplate.defaults['current_user'] = session['current_user']

        # Make data manager available in the request and in the templates
        request.app.datamgr = DataManager(request.environ['beaker.session'],
                                          request.app.config.get('alignak_backend',
                                                                 'http://127.0.0.1:5000'))
        BaseTemplate.defaults['datamgr'] = request.app.datamgr

    logger.info("External request, element type: %s", widget_type)

    if widget_type not in ['files', 'widget', 'table', 'list', 'host', 'service', 'user']:
        logger.warning("External application requested unknown type: %s", widget_type)
        response.status = 409
        response.content_type = 'text/html'
        return _(
            '<div><h1>Unknown required type: %s.</h1>'
            '<p>The required type is unknwown</p></div>' % widget_type
        )

    if widget_type == 'files':
        if identifier == 'js_list':
            response.status = 200
            response.content_type = 'application/json'
            return json.dumps({'status': 'ok', 'files': webui.js_list})
        elif identifier == 'css_list':
            response.status = 200
            response.content_type = 'application/json'
            return json.dumps({'status': 'ok', 'files': webui.css_list})
        else:
            logger.warning("External application requested unknown files: %s", identifier)
            response.status = 409
            response.content_type = 'application/json'
            return json.dumps({'status': 'ko', 'message': "Unknown files list: %s" % identifier})

    if widget_type == 'widget':
        found_widget = None
        for widget in webui.get_widgets_for('external'):
            if identifier == widget['id']:
                found_widget = widget
                break
        else:
            logger.warning("External application requested unknown widget: %s", identifier)
            response.status = 409
            response.content_type = 'text/html'
            return _(
                '<div><h1>Unknown required widget: %s.</h1>'
                '<p>The required widget is not available.</p></div>' % identifier
            )
        logger.debug("Found widget: %s", found_widget)

        embedded_element = found_widget['function'](
            embedded=True,
            identifier=identifier, credentials=credentials
        )

        if request.params.get('page', 'no') == 'no':
            return embedded_element

        return template('external_widget', {
            'embedded_element': embedded_element
        })

    if widget_type == 'table':
        found_table = None
        for table in webui.get_tables_for('external'):
            if identifier == table['id']:
                found_table = table
                break
        else:
            logger.warning("External application requested unknown table: %s", identifier)
            response.status = 409
            response.content_type = 'text/html'
            return _(
                '<div><h1>Unknown required table: %s.</h1>'
                '<p>The required table is not available.</p></div>' % identifier
            )
        logger.info("Found table: %s", found_table)

        if action and action in found_table['actions']:
            logger.info("Required action: %s = %s", action, found_table['actions'][action])
            return found_table['actions'][action]()

        if request.params.get('page', 'no') == 'no':
            return found_table['function'](
                embedded=True, identifier=identifier, credentials=credentials
            )

        return template('external_table', {
            'embedded_element': found_table['function'](
                embedded=True, identifier=identifier, credentials=credentials
            )
        })

    if widget_type == 'list':
        if identifier in webui.lists:
            return webui.lists[identifier]['function'](embedded=True)
        else:
            logger.warning("External application requested unknown list: %s", identifier)
            response.status = 409
            response.content_type = 'text/html'
            return _(
                '<div><h1>Unknown required list: %s.</h1>'
                '<p>The required list is not available.</p></div>' % identifier
            )

    if widget_type in ['host', 'service', 'user']:
        if not action:
            logger.warning(
                "External application requested %s widget without widget name", widget_type
            )
            response.status = 409
            response.content_type = 'text/html'
            return _(
                '<div><h1>Missing %s widget name.</h1>'
                '<p>You must provide a widget name</p></div>' % widget_type
            )

        # Identifier is the element identifier, not the widget one !
        found_widget = None
        for widget in webui.get_widgets_for(widget_type):
            if action == widget['id']:
                found_widget = widget
                break
        else:
            logger.warning("External application requested unknown widget: %s", action)
            response.status = 409
            response.content_type = 'text/html'
            return _(
                '<div><h1>Unknown required widget: %s.</h1>'
                '<p>The required widget is not available.</p></div>' % action
            )
        logger.debug("Found %s widget: %s", widget_type, found_widget)

        if request.params.get('page', 'no') == 'no':
            return found_widget['function'](
                element_id=identifier, widget_id=found_widget['id'],
                embedded=True, identifier=identifier, credentials=credentials
            )

        return template('external_widget', {
            'embedded_element': found_widget['function'](
                element_id=identifier, widget_id=found_widget['id'],
                embedded=True, identifier=identifier, credentials=credentials
            )
        })


# --------------------------------------------------------------------------------------------------
# WebUI user's preferences
# --------------------------------------------------------------------------------------------------
# @app.route('/preferences/user')
# # User preferences page ...
# def show_user_preferences():
#     """
#         Show the user preferences view
#     """
#     return template('_preferences')


@app.route('/preference/user', 'GET')
def get_user_preference():
    """
        Request parameters:

        - key, string identifying the parameter
        - default, default value if parameter does not exist
    """
    user = request.environ['beaker.session']['current_user']
    datamgr = request.app.datamgr

    _key = request.query.get('key', None)
    if not _key:
        return WebUI.response_invalid_parameters(_('Missing mandatory parameters'))

    default = request.query.get('default', None)
    if default:
        default = json.loads(default)

    response.status = 200
    response.content_type = 'application/json'
    return json.dumps(datamgr.get_user_preferences(user, _key, default))


@app.route('/preference/user/delete', 'GET')
def delete_user_preference():
    """
        Request parameters:

        - key, string identifying the parameter
    """
    user = request.environ['beaker.session']['current_user']
    datamgr = request.app.datamgr

    _key = request.query.get('key', None)
    if not _key:
        return WebUI.response_invalid_parameters(_('Missing mandatory parameters'))

    response.status = 200
    response.content_type = 'application/json'
    return json.dumps(datamgr.delete_user_preferences(user, _key))


@app.route('/preference/user', 'POST')
def set_user_preference():
    """
        Request parameters:

        - key, string identifying the parameter
        - value, as a JSON formatted string
    """
    user = request.environ['beaker.session']['current_user']
    datamgr = request.app.datamgr

    _key = request.forms.get('key', None)
    _value = request.forms.get('value', None)
    if _key is None or _value is None:
        return WebUI.response_invalid_parameters(_('Missing mandatory parameters'))

    if datamgr.set_user_preferences(user, _key, json.loads(_value)):
        return WebUI.response_ok(message=_('User preferences saved'))
    else:
        return WebUI.response_ko(
            message=_('Problem encountered while saving common preferences')
        )


@app.error(403)
def mistake403(code):  # pylint: disable=unused-argument
    """HTTP error code 403"""
    return 'There is a mistake in your url!'


@app.error(404)
def mistake404(code):  # pylint: disable=unused-argument
    """HTTP error code 404"""
    return 'Sorry, this page does not exist!'


# Bottle templates path
TEMPLATE_PATH.append(
    os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'views'
    )
)

# -----
# Extend default WSGI application with a session middleware
# -----
session_opts = {
    'session.type': app.config.get('session.type', 'file'),
    'session.data_dir': app.config.get('session.data_dir',
                                       os.path.join('/tmp', __manifest__['name'], 'sessions')),
    'session.auto': app.config.get('session.auto', True),
    'session.cookie_expires': app.config.get('session.cookie_expires', 43200),
    'session.key': app.config.get('session.key', __manifest__['name']),
    'session.save_accessed_time': True,
    'session.timeout': app.config.get('session.timeout', None),
    'session.data_serializer': app.config.get('session.data_serializer', 'json'),
    # Do not remove! For unit tests only...
    'sesssion.webtest_varname': __manifest__['name'],
}
logger.debug("Session parameters: %s" % session_opts)
session_app = SessionMiddleware(app, session_opts)

if __name__ == '__main__':
    run(
        app=session_app,
        host=app.config.get('host', '127.0.0.1'),
        port=int(app.config.get('port', 5001)),
        debug=app.config.get('debug', False),
        reloader=app.config.get('debug', False)
    )
    # remember to remove reloader=True and debug(True) when you move your application
    # from development to a production environment
