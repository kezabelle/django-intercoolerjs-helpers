# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import wrapt
from django.utils import inspect
from .helpers import push_url_modifier, default_path_handler, redirect_modifier


class ic_push_url(object):
    def __init__(self, path_handler, keep_querystring_keys=None):
        path_handler_argspec = inspect.getargspec(path_handler)
        path_handler_args = path_handler_argspec[0]
        if not path_handler_args:
            raise TypeError("path_handler is missing the argument `request`")
        elif path_handler_args[0] != 'request':
            raise TypeError("path_handler's first argument must be `request`")
        self.path_handler = path_handler
        if keep_querystring_keys is None:
            keep_querystring_keys = ('*',)
        self.keep_querystring_keys = keep_querystring_keys

    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        def get_request(*_args, **_kwargs):
            return _args[0]
        request = get_request(*args, **kwargs)
        response = wrapped(*args, **kwargs)
        if not request.is_intercooler():
            return response
        push_url_modifier(request=request, response=response,
                          path_handler=self.path_handler,
                          keep_querystring_keys=self.keep_querystring_keys)
        return response


class ic_push_current_url(ic_push_url):
    def __init__(self, keep_querystring_keys=None):
        path_handler = default_path_handler
        super(ic_push_current_url, self).__init__(
            path_handler=path_handler,
            keep_querystring_keys=keep_querystring_keys
        )


class ic_redirect(object):
    def __init__(self, keep_headers=None):
        if keep_headers is None:
            keep_headers = ('*',)
        self.keep_headers = keep_headers

    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        def get_request(*_args, **_kwargs):
            return _args[0]
        request = get_request(*args, **kwargs)
        response = wrapped(*args, **kwargs)
        if not request.is_intercooler():
            return response
        replacement_response = redirect_modifier(response, keep_headers=self.keep_headers)
        return replacement_response
