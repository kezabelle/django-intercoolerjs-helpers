# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from collections import namedtuple
from contextlib import contextmanager
from types import MethodType

from django.http import QueryDict, HttpResponse
from django.urls import Resolver404
from django.urls import resolve
from django.utils.functional import SimpleLazyObject
from django.utils.six.moves.urllib.parse import urlparse
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # < Django 1.10
    class MiddlewareMixin(object):
        pass


__all__ = ['IntercoolerMiddleware', 'HttpMethodOverride']


class HttpMethodOverride(MiddlewareMixin):
    """
    Support for X-HTTP-Method-Override and _method=PUT style request method
    changing.

    Note: if https://pypi.python.org/pypi/django-method-override gets updated
    with support for newer Django (ie: implements MiddlewareMixin), without
    dropping older versions, I could possibly replace this with that.
    """
    def process_request(self, request):
        request.changed_method = False
        if request.method != 'POST':
            return
        methods = {'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'}
        potentials = ((request.GET, '_method'),
                      (request.META, 'HTTP_X_HTTP_METHOD_OVERRIDE'))
        for querydict, key in potentials:
            if key in querydict and querydict[key].upper() in methods:
                request.original_method = request.method
                request.method = querydict[key].upper()
                request.changed_method = True
                return


def _maybe_intercooler(self):
    return self.META.get('HTTP_X_IC_REQUEST') == 'true'


def _is_intercooler(self):
    return self.is_ajax() and self.maybe_intercooler()


@contextmanager
def _mutate_querydict(qd):
    qd._mutable = True
    yield qd
    qd._mutable = False


NameId = namedtuple('NameId', 'name id')
UrlMatch = namedtuple('UrlMatch', 'url match')


class IntercoolerQueryDict(QueryDict):
    @property
    def url(self):
        url = self.get('ic-current-url', None)
        match = None
        if url is not None:
            url = url.strip()
            url = urlparse(url)
            if url.path:
                try:
                    match = resolve(url.path)
                except Resolver404:
                    pass
        return UrlMatch(url, match)

    current_url = url

    @property
    def element(self):
        return NameId(self.get('ic-element-name', None), self.get('ic-element-id', None))

    @property
    def id(self):
        # I know IC calls it a UUID internally, buts its just 1, incrementing.
        return int(self.get('ic-id', '0'))

    @property
    def request(self):
        return bool(self.get('ic-request', None))

    @property
    def target_id(self):
        return self.get('ic-target-id', None)

    @property
    def trigger(self):
        return NameId(self.get('ic-trigger-name', None), self.get('ic-trigger-id', None))

    @property
    def prompt_value(self):
        return self.get('ic-prompt-value', None)


def intercooler_data(self):
    if not hasattr(self, '_processed_intercooler_data'):
        IC_KEYS = ['ic-current-url', 'ic-element-id', 'ic-element-name',
                   'ic-id', 'ic-prompt-value', 'ic-target-id',
                   'ic-trigger-id', 'ic-trigger-name', 'ic-request']
        ic_qd = IntercoolerQueryDict('', encoding=self.encoding)
        with _mutate_querydict(ic_qd) as IC_DATA:
            # For a little while, we need to pop data out of request.GET
            with _mutate_querydict(self.GET) as GET:
                for ic_key in IC_KEYS:
                    if ic_key in GET:
                        # emulate how .get() behaves, because pop returns the
                        # whole shebang.
                        try:
                            removed = GET.pop(ic_key)[-1]
                        except IndexError:
                            removed = []
                        IC_DATA.update({ic_key: removed})
            # Don't pop these ones off, so that decisions can be made for
            # handling _method
            ic_request = GET.get('_method')
            IC_DATA.update({'_method': ic_request})
            # If HttpMethodOverride is in the middleware stack, this may
            # return True.
            IC_DATA.changed_method = getattr(self, 'changed_method', False)
        self._processed_intercooler_data = ic_qd
    return self._processed_intercooler_data


class IntercoolerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.maybe_intercooler = _maybe_intercooler.__get__(request)
        request.is_intercooler = _is_intercooler.__get__(request)
        request.intercooler_data = SimpleLazyObject(intercooler_data.__get__(request))



class IntercoolerRedirector(MiddlewareMixin):
    def process_response(self, request, response):
        if not request.is_intercooler():
            return response
        if response.status_code > 300 and response.status_code < 400:
            if response.has_header('Location'):
                url = response['Location']
                del response['Location']
                new_resp = HttpResponse()
                for k, v in response.items():
                    new_resp[k] = v
                new_resp['X-IC-Redirect'] = url
                return new_resp
        return response
