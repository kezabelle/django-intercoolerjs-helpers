# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from contextlib import contextmanager
from django.utils.encoding import escape_uri_path
from django.http import QueryDict, HttpResponse


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
            set(keep_headers) == {'*'}
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
