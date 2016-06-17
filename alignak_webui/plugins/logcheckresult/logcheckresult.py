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
    Plugin Log check result
"""

import time
import json

from collections import OrderedDict

from logging import getLogger
from bottle import request, response, redirect

from alignak_webui.objects.item import Item

from alignak_webui.utils.datatable import Datatable

logger = getLogger(__name__)

# Will be populated by the UI with it's own value
webui = None

# Get the same schema as the applications backend and append information for the datatable view
# Use an OrderedDict to create an ordered list of fields
schema = OrderedDict()
# Specific field to include the responsive + button used to display hidden columns on small devices
schema['#'] = {
    'type': 'string',
    'ui': {
        'title': '',
        # This field is visible (default: False)
        'visible': True,
        # This field is initially hidden (default: False)
        'hidden': False,
        # This field is searchable (default: True)
        'searchable': False,
        # This field is orderable (default: True)
        'orderable': False,
        # search as a regex (else strict value comparing when searching is performed)
        'regex': False,
        # defines the priority for the responsive column hidding (0 is the most important)
        # Default is 10000
        # 'priority': 0,
    }
}
schema['host'] = {
    'type': 'objectid',
    'ui': {
        'title': _('Host'),
        'width': '10',
        'visible': True,
        'hidden': True,
    },
    'data_relation': {
        'resource': 'host',
        'embeddable': True
    }
}
schema['service'] = {
    'type': 'objectid',
    'ui': {
        'title': _('Service'),
        'width': '10px',
        'visible': True,
        'hidden': True,
    },
    'data_relation': {
        'resource': 'service',
        'embeddable': True
    }
}
schema['state'] = {
    'type': 'string',
    'ui': {
        'title': _('State'),
        'visible': True,
        'size': 5,
        # 'priority': 0,
    },
    'allowed': ["OK", "WARNING", "CRITICAL", "UNKNOWN", "UP", "DOWN", "UNREACHABLE"]
}
schema['state_type'] = {
    'type': 'string',
    'ui': {
        'title': _('State type'),
        'visible': True,
        # 'priority': 0,
    },
    'allowed': ["HARD", "SOFT"]
}
schema['state_id'] = {
    'type': 'integer',
    'ui': {
        'title': _('State identifier'),
        'visible': True,
        'hidden': True
    },
    'allowed': ['0', '1', '2', '3', '4']
}
schema['acknowledged'] = {
    'type': 'boolean',
    'ui': {
        'title': _('Acknowledged'),
        'visible': True,
        'size': 2,
    },
}
schema['last_check'] = {
    'type': 'integer',
    'ui': {
        'title': _('Last check'),
        'visible': True
    },
}
schema['last_state'] = {
    'type': 'string',
    'ui': {
        'title': _('Last state'),
        'visible': True,
        'hidden': True
    },
    'allowed': ["OK", "WARNING", "CRITICAL", "UNKNOWN", "UP", "DOWN", "UNREACHABLE"]
}
schema['output'] = {
    'type': 'string',
    'ui': {
        'title': _('Check output'),
        'visible': True
    },
}
schema['long_output'] = {
    'type': 'string',
    'ui': {
        'title': _('Check long output'),
        'visible': True
    },
}
schema['perf_data'] = {
    'type': 'string',
    'ui': {
        'title': _('Performance data'),
        'visible': True
    },
}
schema['latency'] = {
    'type': 'float',
    'ui': {
        'title': _('Latency'),
        'visible': True,
        'hidden': True
    },
}
schema['execution_time'] = {
    'type': 'float',
    'ui': {
        'title': _('Execution time'),
        'visible': True,
        'hidden': True
    },
}


# This to define the global information for the table
schema['ui'] = {
    'type': 'boolean',
    'default': True,

    # UI parameters for the objects
    'ui': {
        'page_title': _('Log check result table (%d items)'),
        'uid': '_id',
        'visible': True,
        'orderable': True,
        'editable': False,
        'selectable': True,
        'searchable': True,
        'responsive': False
    }
}


def get_logcheckresult_table():
    """
    Get the logcheckresult list and transform it as a table
    """
    datamgr = request.environ['beaker.session']['datamanager']

    # Pagination and search
    where = webui.helper.decode_search(request.query.get('search', ''))

    # Get total elements count
    total = datamgr.get_objects_count('logcheckresult', search=where)

    # Build table structure
    dt = Datatable('logcheckresult', datamgr.backend, schema)

    title = dt.title
    if '%d' in title:
        title = title % total

    return {
        'object_type': 'logcheckresult',
        'dt': dt,
        'title': request.query.get('title', title)
    }


def get_logcheckresult_table_data():
    """
    Get the logcheckresult list and provide table data
    """
    datamgr = request.environ['beaker.session']['datamanager']
    dt = Datatable('logcheckresult', datamgr.backend, schema)

    response.status = 200
    response.content_type = 'application/json'
    return dt.table_data()


def get_logcheckresult(element_id):
    """
    Display the element linked to a logcheckresult item
    """
    datamgr = request.environ['beaker.session']['datamanager']

    element = datamgr.get_logcheckresult({'where': {'_id': element_id}})
    if not element:  # pragma: no cover, should not happen
        return webui.response_invalid_parameters(_('Log check result element does not exist'))

    element = element[0]
    if element['type'] == 'host':
        logger.debug("Log check result: %s %s %s", element, element.host.id, element.__dict__)
        redirect('/host/' + element.host.id)
    else:
        logger.debug("Log check result: %s %s %s", element, element.host.id, element.__dict__)
        redirect('/host/' + element.host.id + '#services')


pages = {
    get_logcheckresult: {
        'name': 'Log check result',
        'route': '/logcheckresult/<element_id>'
    },
    get_logcheckresult_table: {
        'name': 'Log check result table',
        'route': '/logcheckresult_table',
        'view': '_table'
    },

    get_logcheckresult_table_data: {
        'name': 'Log check result table data',
        'route': '/logcheckresult_table_data',
        'method': 'POST'
    },
}