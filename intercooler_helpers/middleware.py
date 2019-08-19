# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from collections import namedtuple
from contextlib import contextmanager

from django.http import QueryDict, HttpResponse
from django.urls import Resolver404, resolve
from django.utils.functional import SimpleLazyObject
from django.utils.six.moves.urllib.parse import urlparse
from django.utils.deprecation import MiddlewareMixin


__all__ = ['IntercoolerData', 'HttpMethodOverride']


class HttpMethodOverride(MiddlewareMixin):
    """
    Support for X-HTTP-Method-Override and _method=PUT style request method
    changing.

    Note: if https://pypi.python.org/pypi/django-method-override gets updated
    with support for newer Django (ie: implements MiddlewareMixin), without
    dropping older versions, I could possibly replace this with that.
    """
    caring_methods = ['POST']
    target_methods = {'POST', 'PUT', 'PATCH', 'DELETE'}

    def process_request(self, request):
        request.changed_method = False
        if request.method in self.caring_methods: pass
        else:
            return
        methods = self.target_methods
        potentials = ((request.META, 'HTTP_X_HTTP_METHOD_OVERRIDE'),
                      (request.GET, '_method'),
                      (request.POST, '_method'))
        for querydict, key in potentials:
            if key in querydict and querydict[key].upper() in methods:
                newmethod = querydict[key].upper()
                # Don't change the method data if the calling method was
                # the same as the intended method.
                if newmethod == request.method:
                    return
                else: pass
                request.original_method = request.method
                if hasattr(querydict, '_mutable'):
                    with _mutate_querydict(querydict):
                        querydict.pop(key)
                # ```This could not be tested so may be never happen!
                # if hasattr(request, newmethod): pass
                # else:
                setattr(request, newmethod, request.POST)
                # ```
                request.method = newmethod
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

    def __repr__(self):
        props = ('id', 'request', 'target_id', 'element', 'trigger',
                 'prompt_value', 'url')
        attrs = ['{name!s}={val!r}'.format(name=prop, val=getattr(self, prop))
                 for prop in props]
        return "<{cls!s}: {attrs!s}>".format(cls=self.__class__.__name__,
                                             attrs=", ".join(attrs))


def intercooler_data(self):
    try:
        return self._processed_intercooler_data
    except AttributeError: pass
    IC_KEYS = ['ic-current-url', 'ic-element-id', 'ic-element-name',
               'ic-id', 'ic-prompt-value', 'ic-target-id',
               'ic-trigger-id', 'ic-trigger-name', 'ic-request']
    ic_qd = IntercoolerQueryDict('', encoding=self.encoding)
    if self.method in ('GET', 'HEAD', 'OPTIONS'):
        query_params = self.GET
    else:
        query_params = self.POST
    query_keys = tuple(query_params.keys())
    for ic_key in IC_KEYS:
        if ic_key in query_keys:
            # emulate how .get() behaves, because pop returns the
            # whole shebang.
            # For a little while, we need to pop data out of request.GET
            with _mutate_querydict(query_params) as REQUEST_DATA:
                try:
                    removed = REQUEST_DATA.pop(ic_key)[-1]
                except IndexError: # pragma: no cover, for safe guard only
                    removed = []
            with _mutate_querydict(ic_qd) as IC_DATA:
                IC_DATA.update({ic_key: removed})
    # Don't pop these ones off, so that decisions can be made for
    # handling _method
    ic_request = query_params.get('_method')
    with _mutate_querydict(ic_qd) as IC_DATA:
        IC_DATA.update({'_method': ic_request})
    # If HttpMethodOverride is in the middleware stack, this may
    # return True.
    IC_DATA.changed_method = getattr(self, 'changed_method', False)
    self._processed_intercooler_data = ic_qd
    return ic_qd


class IntercoolerData(MiddlewareMixin):
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
