#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016:
#   Frederic Mohier, frederic.mohier@gmail.com
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
    Plugin actions
"""

from logging import getLogger

from bottle import request

from alignak_webui import _
from alignak_webui.utils.plugin import Plugin

logger = getLogger(__name__)


class PluginActions(Plugin):
    """ Actions plugin """

    def __init__(self, app, cfg_filenames=None):
        """
        Actions plugin
        """
        self.name = 'Actions'
        self.backend_endpoint = None

        self.pages = {
            'show_acknowledge_add': {
                'name': 'Acknowledge add form',
                'route': '/acknowledge/form/add',
                'view': 'acknowledge_form_add'
            },
            'add_acknowledge': {
                'name': 'Acknowledge',
                'route': '/acknowledge/add',
                'method': 'POST'
            },
            'show_recheck_add': {
                'name': 'Recheck add form',
                'route': '/recheck/form/add',
                'view': 'recheck_form_add'
            },
            'add_recheck': {
                'name': 'Recheck',
                'route': '/recheck/add',
                'method': 'POST'
            },
            'show_downtime_add': {
                'name': 'Downtime add form',
                'route': '/downtime/form/add',
                'view': 'downtime_form_add'
            },
            'add_downtime': {
                'name': 'Downtime',
                'route': '/downtime/add',
                'method': 'POST'
            }
        }

        super(PluginActions, self).__init__(app, cfg_filenames)

    def show_acknowledge_add(self):
        """
            Show form to add an acknowledge
        """
        return {
            'title': request.query.get('title', _('Request an acknowledge')),
            'action': request.query.get('action', 'add'),
            'elements_type': request.query.get('elements_type'),
            'element_id': request.query.getall('element_id'),
            'element_name': request.query.getall('element_name'),
            'sticky': request.query.get('sticky', '1') == '1',
            'notify': request.query.get('notify', '1') == '1',
            'persistent': request.query.get('persistent', '1') == '1',
            'comment': request.query.get('comment', _('Acknowledge requested from WebUI')),
            'read_only': request.query.get('read_only', '0') == '1',
            'auto_post': request.query.get('auto_post', '0') == '1'
        }

    def add_acknowledge(self):
        """
        Add an acknowledgement

        Parameters:
        - element_id[]: all the livestate elements identifiers to be acknowledged

        - sticky
        - notify
        - persistent
        - comment

        """
        user = request.environ['beaker.session']['current_user']
        datamgr = request.app.datamgr

        element_ids = request.forms.getall('element_id')
        if not element_ids:
            logger.error("request to send an acknowledge: missing element_id parameter!")
            return self.webui.response_invalid_parameters(
                _('Missing element identifier: element_id')
            )

        problem = False
        status = ""

        # Method to get elements from the data manager
        elements_type = request.forms.get('elements_type', 'host')
        f = getattr(datamgr, 'get_%s' % elements_type)
        if not f:
            status += (_("No method to get a %s element") % elements_type)
        else:
            for element_id in element_ids:
                element = f(element_id)
                if not element:
                    status += _('%s element %s does not exist') % (elements_type, element_id)
                    continue

                # Prepare post request ...
                data = {
                    'action': 'add',
                    'host': element.id,
                    'service': None,
                    'user': user.id,
                    'sticky': request.forms.get('sticky', 'false') == 'true',
                    'notify': request.forms.get('notify', 'false') == 'true',
                    'persistent': request.forms.get('persistent', 'false') == 'true',
                    'comment': request.forms.get('comment', _('No comment'))
                }
                if elements_type == 'service':
                    data.update({'host': element.host.id, 'service': element.id})

                if not datamgr.add_acknowledge(data=data):
                    status += _("Failed adding an acknowledge for %s") % element.name
                    problem = True
                else:
                    if elements_type == 'service':
                        data.update({'host': element.host.id, 'service': element.id})
                        status += _('Acknowledge sent for %s/%s.') % \
                            (element.host.name, element.name)
                    else:
                        status += _('Acknowledge sent for %s.') % \
                            element.name

        logger.info("Request an acknowledge, result: %s", status)

        if not problem:
            return self.webui.response_ok(message=status)
        else:
            return self.webui.response_ko(message=status)

    def show_recheck_add(self):
        """
            Show form to request a forced check
        """
        return {
            'title': request.query.get('title', _('Send a check request')),
            'elements_type': request.query.get('elements_type'),
            'element_id': request.query.getall('element_id'),
            'element_name': request.query.getall('element_name'),
            'comment': request.query.get('comment', _('Re-check requested from WebUI')),
            'read_only': request.query.get('read_only', '0') == '1',
            'auto_post': request.query.get('auto_post', '0') == '1'
        }

    def add_recheck(self):
        """
        Request a forced check
        """
        user = request.environ['beaker.session']['current_user']
        datamgr = request.app.datamgr

        element_ids = request.forms.getall('element_id')
        if not element_ids:
            logger.error("request to send an recheck: missing element_id parameter!")
            return self.webui.response_invalid_parameters(
                _('Missing element identifier: element_id')
            )

        problem = False
        status = ""

        # Method to get elements from the data manager
        elements_type = request.forms.get('elements_type', 'host')
        f = getattr(datamgr, 'get_%s' % elements_type)
        if not f:
            status += (_("No method to get a %s element") % elements_type)
        else:
            for element_id in element_ids:
                element = f(element_id)
                if not element:
                    status += _('%s element %s does not exist') % (elements_type, element_id)
                    continue

                # Prepare post request ...
                data = {
                    'host': element.id,
                    'service': None,
                    'user': user.id,
                    'comment': request.forms.get('comment', _('No comment'))
                }
                if elements_type == 'service':
                    data.update({'host': element.host.id, 'service': element.id})

                if not datamgr.add_recheck(data=data):
                    status += _("Failed adding a check request for %s") % element.name
                    problem = True
                else:
                    if elements_type == 'service':
                        data.update({'host': element.host.id, 'service': element.id})
                        status += _('Check request sent for %s/%s.') % \
                            (element.host.name, element.name)
                    else:
                        status += _('Check request sent for %s.') % \
                            element.name

        logger.info("Request a re-check, result: %s", status)

        if not problem:
            return self.webui.response_ok(message=status)
        else:
            return self.webui.response_ko(message=status)

    def show_downtime_add(self):
        """
            Show form to add a downtime
        """
        return {
            'title': request.query.get('title', _('Request a downtime')),
            'action': request.query.get('action', 'add'),
            'elements_type': request.query.get('elements_type'),
            'element_id': request.query.getall('element_id'),
            'element_name': request.query.getall('element_name'),
            'start_time': request.query.get('start_time'),
            'end_time': request.query.get('end_time'),
            'fixed': request.query.get('fixed', '1') == '1',
            'duration': request.query.get('duration', 86400),
            'comment': request.query.get('comment', _('Downtime requested from WebUI')),
            'read_only': request.query.get('read_only', '0') == '1',
            'auto_post': request.query.get('auto_post', '0') == '1'
        }

    def add_downtime(self):
        """
        Add a downtime
        """
        user = request.environ['beaker.session']['current_user']
        datamgr = request.app.datamgr

        element_ids = request.forms.getall('element_id')
        if not element_ids:
            logger.error("request to send an downtime: missing element_id parameter!")
            return self.webui.response_invalid_parameters(
                _('Missing element identifier: element_id')
            )

        problem = False
        status = ""

        # Method to get elements from the data manager
        elements_type = request.forms.get('elements_type', 'host')
        f = getattr(datamgr, 'get_%s' % elements_type)
        if not f:
            status += (_("No method to get a %s element") % elements_type)
        else:
            for element_id in element_ids:
                element = f(element_id)
                if not element:
                    status += _('%s element %s does not exist') % (elements_type, element_id)
                    continue

                # Prepare post request ...
                data = {
                    'action': 'add',
                    'host': element.id,
                    'service': None,
                    'user': user.id,
                    'start_time': request.forms.get('start_time'),
                    'end_time': request.forms.get('end_time'),
                    'fixed': request.forms.get('fixed', 'false') == 'true',
                    'duration': int(request.forms.get('duration', '86400')),
                    'comment': request.forms.get('comment', _('No comment'))
                }
                if elements_type == 'service':
                    data.update({'host': element.host.id, 'service': element.id})

                logger.critical("Request a downtime, data: %s", data)
                if not datamgr.add_downtime(data=data):
                    status += _("Failed adding a downtime for %s") % element.name
                    problem = True
                else:
                    if elements_type == 'service':
                        data.update({'host': element.host.id, 'service': element.id})
                        status += _('Downtime sent for %s/%s.') % \
                            (element.host.name, element.name)
                    else:
                        status += _('Downtime sent for %s.') % \
                            element.name

        logger.info("Request a downtime, result: %s", status)

        if not problem:
            return self.webui.response_ok(message=status)
        else:
            return self.webui.response_ko(message=status)
