# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import logging
import warnings
from contextlib import contextmanager

from django.http import QueryDict, HttpResponse
from django.utils.encoding import escape_uri_path

try:
    from pyquery import PyQuery
    from lxml import etree
    CAN_PYQUERY = True
except ImportError:
    CAN_PYQUERY = False


logger = logging.getLogger(__name__)


def default_path_handler(request):
    return request.path


@contextmanager
def _mutate_querydict(qd):
    qd._mutable = True
    yield qd
    qd._mutable = False


def extract_querystring_keys(querydict, keys):
    new_querydict = QueryDict('', mutable=True)
    with _mutate_querydict(new_querydict) as qd:
        if set(keys) == {'*'}:
            qd.update(querydict)
        else:
            for key in keys:
                if key in querydict:
                    qd.update(**{key:querydict[key]})
    return new_querydict


def push_url_modifier(request, response, path_handler, keep_querystring_keys):
    header_name = 'X-IC-PushURL'
    if not response.has_header(header_name):
        path = escape_uri_path(path_handler(request=request))
        keep_query = extract_querystring_keys(querydict=request.GET,
                                              keys=keep_querystring_keys)
        querystring = keep_query.urlencode()
        if querystring:
            querystring = '?%s' % (querystring,)
        response[header_name] = '%s%s' % (path, querystring)


def redirect_modifier(response, keep_headers):
    header_name = 'X-IC-Redirect'
    if response.status_code > 300 and response.status_code < 400:
        # is a redirect, but missing the client-side portion.
        if response.has_header('Location') and not response.has_header(header_name):
            url = response['Location']
            del response['Location']
            new_resp = HttpResponse()
            for k, v in response.items():
                # keep any headers (other than Location)
                if set(keep_headers) == {'*'}:
                    new_resp[k] = v
                else:
                    # keep only the filtered headers we want.
                    if k in keep_headers:
                        new_resp[k] = v
            new_resp[header_name] = url
            return new_resp
    return response

if CAN_PYQUERY:

    def select_from_response_modifier(request, response):
        content_type = response['Content-Type'][0:10]
        if content_type not in ("text/html", 'text/html;'):
            return response
        try:
            tree = PyQuery(response.content)
        except (etree.XMLSyntaxError, etree.ParserError) as e:
            logger.exception(
                "Failed to parse potential HTML content",
                exc_info=e, extra={'request': request,
                                   'status_code': response.status_code
                                   })
            return response
        else:
            selector = request.intercooler_data.select_from_response
            if selector:
                inner_html = tree(selector)
                if not inner_html:
                    logger.warning("Intercooler requested selector: `{}` for "
                                   "which pyquery returned "
                                   "0 results".format(selector),
                                   extra={'request': request,
                                   'status_code': response.status_code})
                    return response
                element_count = len(inner_html)
                if not element_count == 1:
                    logger.warning("Intercooler requested selector: `{}` "
                                   "which returned "
                                   "{} results.".format(selector, element_count),
                                   extra={'request': request,
                                   'status_code': response.status_code})
                    return response
                outer_html = inner_html.eq(0).outerHtml()
                if not outer_html:
                    logger.warning("Intercooler requested the parent element "
                                   "for selector: `{}`, and pyquery returned "
                                   "0 results".format(selector),
                                   extra={'request': request,
                                          'status_code': response.status_code})
                    return response
                response.content = outer_html
                header_name = 'X-IC-Title'
                if not response.has_header(header_name):
                    title = tree.find('head > title:first')
                    if title:
                        response[header_name] = title.eq(0).text()
            return response

else:

    def select_from_response_modifier(request, response):
        warnings.warn("missing pyquery or lxml package, relying on Intercooler's client-side HTML parsing.")
        return response
