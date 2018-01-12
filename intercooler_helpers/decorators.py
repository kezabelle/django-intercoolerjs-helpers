# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from functools import partial
import wrapt
from django.utils.decorators import decorator_from_middleware

from intercooler_helpers.helpers import (select_from_response_modifier,
                                         redirect_modifier)
from intercooler_helpers.middleware import IntercoolerData


def get_request(*args, **kwargs):
    return args[0]
#
# class ic_push_url(object):
#     def __init__(self, path_handler, keep_querystring_keys=None):
#         path_handler_argspec = inspect.getargspec(path_handler)
#         path_handler_args = path_handler_argspec[0]
#         if not path_handler_args:
#             raise TypeError("path_handler is missing the argument `request`")
#         elif path_handler_args[0] != 'request':
#             raise TypeError("path_handler's first argument must be `request`")
#         self.path_handler = path_handler
#         if keep_querystring_keys is None:
#             keep_querystring_keys = ('*',)
#         self.keep_querystring_keys = keep_querystring_keys
#
#     @wrapt.decorator
#     def __call__(self, wrapped, instance, args, kwargs):
#         request = get_request(*args, **kwargs)
#         response = wrapped(*args, **kwargs)
#         if not request.is_intercooler():
#             return response
#         push_url_modifier(request=request, response=response,
#                           path_handler=self.path_handler,
#                           keep_querystring_keys=self.keep_querystring_keys)
#         return response
#
#
# class ic_push_current_url(ic_push_url):
#     def __init__(self, keep_querystring_keys=None):
#         path_handler = default_path_handler
#         super(ic_push_current_url, self).__init__(
#             path_handler=path_handler,
#             keep_querystring_keys=keep_querystring_keys
#         )
#
# def ic_push_url(path_handler, keep_querystring_keys=None):
#     import pdb; pdb.set_trace()
#     path_handler_argspec = inspect.getargspec(path_handler)
#     path_handler_args = path_handler_argspec[0]
#     if not path_handler_args:
#         raise TypeError("path_handler is missing the argument `request`")
#     elif path_handler_args[0] != 'request':
#         raise TypeError("path_handler's first argument must be `request`")
#     if keep_querystring_keys is None:
#         keep_querystring_keys = ('*',)
#
#     @wrapt.decorator
#     def _ic_push_url(self, wrapped, instance, args, kwargs):
#         response = wrapped(*args, **kwargs)
#         request = get_request(*args, **kwargs)
#         if not request.is_intercooler():
#             return response
#         push_url_modifier(request=request, response=response,
#                           path_handler=path_handler,
#                           keep_querystring_keys=keep_querystring_keys)
#         return response
#
#     return _ic_push_url

# ic_push_current_url = ic_push_url()

def ic_redirect(wrapped=None, keep_headers=None):
    if wrapped is None:
        return partial(ic_redirect, keep_headers=keep_headers)

    if keep_headers is None:
        keep_headers = ('*',)

    @wrapt.decorator
    def _ic_redirect(wrapped, instance, args, kwargs):
        response = wrapped(*args, **kwargs)
        request = get_request(*args, **kwargs)
        if not hasattr(request, 'is_intercooler'):
            return response
        if not request.is_intercooler():
            return response
        replacement_response = redirect_modifier(response, keep_headers=keep_headers)
        return replacement_response

    return _ic_redirect(wrapped)


def ic_select_from_response(wrapped=None):
    if wrapped is None:
        return ic_select_from_response

    @wrapt.decorator
    def _ic_select_from_response(wrapped, instance, args, kwargs):
        response = wrapped(*args, **kwargs)
        request = get_request(*args, **kwargs)
        if not hasattr(request, 'is_intercooler'):
            return response
        if not request.is_intercooler():
            return response
        select_from_response_modifier(request=request, response=response)
        return response

    return _ic_select_from_response(wrapped)

ic_data = decorator_from_middleware(IntercoolerData)
