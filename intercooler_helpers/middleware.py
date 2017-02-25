# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from collections import namedtuple
from contextlib import contextmanager
from types import MethodType

from django.http import QueryDict

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # < Django 1.10
    class MiddlewareMixin(object):
        pass


__all__ = ['IntercoolerMiddleware']


def _maybe_intercooler(self):
    return 'ic-request' in self.GET


def _is_intercooler(self):
    return self.is_ajax() and self.maybe_intercooler()


@contextmanager
def _mutate_querydict(qd):
    qd._mutable = True
    yield qd
    qd._mutable = False


class HttpMethodChange(namedtuple('HttpMethodChange', 'original target')):
    def should_change(self):
        return self.original != self.target


def maybe_change_http_method(request):
    methods = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS')
    if '_method' in request.GET and request.GET['_method'].upper() in methods:
        request.original_method = request.method
        return HttpMethodChange(request.method, request.GET['_method'].upper())
    return HttpMethodChange(request.method, request.method)

NameId = namedtuple('NameId', 'name id')


class IntercoolerQueryDict(QueryDict):
    @property
    def current_url(self):
        return self.get('ic-current-url', None)

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
                   'ic-trigger-id', 'ic-trigger-name']
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
            # Don't pop these ones off, so that maybe_intercooler can be called
            # subsequent to consuming the IC data, and so that decisions
            # can be made for handling _method
            for key in ('ic-request', '_method'):
                ic_request = GET.get(key)
                IC_DATA.update({key: ic_request})
            # This key should always exist on any intercooler request,
            IC_DATA.changed_method = getattr(self, 'changed_method', False)
        self._processed_intercooler_data = ic_qd
    return self._processed_intercooler_data


class IntercoolerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.maybe_intercooler = MethodType(_maybe_intercooler, request)
        request.is_intercooler = MethodType(_is_intercooler, request)
        request.intercooler_data = MethodType(intercooler_data, request)
        # If Intercooler sent a request, and used the _method=XXX to indicate
        # a PUT/PATCH etc ... change it.
        if request.is_intercooler():
            method = maybe_change_http_method(request)
            if method.should_change():
                request.original_method = method.original
                request.method = method.target
                request.changed_method = True
