# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import pytest
from intercooler_helpers.middleware import (IntercoolerMiddleware,
                                            HttpMethodOverride)


@pytest.fixture
def ic_mw():
    return IntercoolerMiddleware()

@pytest.fixture
def http_method_mw():
    return HttpMethodOverride()


@pytest.mark.parametrize("method", [
    "maybe_intercooler",
    "is_intercooler",
    "intercooler_data",
    "_processed_intercooler_data",
])
def test_methods_dont_exist_on_class_only_on_instance(rf, ic_mw, method):
    request = rf.get('/')
    ic_mw.process_request(request)
    assert request.intercooler_data.id == 0
    assert hasattr(request, method) is True
    assert hasattr(request.__class__, method) is False


def test_maybe_intercooler_via_header(rf, ic_mw):
    request = rf.get('/', HTTP_X_IC_REQUEST="true")
    ic_mw.process_request(request)
    assert request.maybe_intercooler() is True


def test_maybe_intercooler_old_way(rf, ic_mw):
    request = rf.get('/', data={'ic-request': 'true'})
    ic_mw.process_request(request)
    assert request.maybe_intercooler() is False


def test_is_intercooler(rf, ic_mw):
    request = rf.get('/', HTTP_X_IC_REQUEST="true",
                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    ic_mw.process_request(request)
    assert request.is_intercooler() is True


def test_intercooler_data(rf, ic_mw):
    querystring_data = {
        'ic-id': '3',
        'ic-request': 'true',
        'ic-element-id': 'html_id',
        'ic-element-name': 'html_name',
        'ic-target-id': 'target_html_id',
        'ic-trigger-id': 'triggered_by_id',
        'ic-trigger-name': 'triggered_by_html_name',
        'ic-current-url': '/lol/',
        # This is undocumented at the time of writing, and only turns up
        # if no ic-prompt-name is given on the request to inflight.
        'ic-prompt-value': 'undocumented',
        # This may be set if not using
        # <meta name="intercoolerjs:use-actual-http-method" content="true"/>
        '_method': 'POST',
    }
    request = rf.get('/', data=querystring_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    ic_mw.process_request(request)
    # Before running, this attribute should not exist.
    with pytest.raises(AttributeError):
        request._processed_intercooler_data
    data = request.intercooler_data
    assert data.current_url == '/lol/'
    assert data.element == ('html_name', 'html_id')
    assert data.id == 3
    assert data.request is True
    assert data.target_id == 'target_html_id'
    assert data.trigger == ('triggered_by_html_name', 'triggered_by_id')
    assert data.prompt_value == 'undocumented'
    assert data._mutable is False
    assert data.dict() == querystring_data
    # ensure that after calling the property (well, SimpleLazyObject)
    # the request has cached the data structure to an attribute.
    request._processed_intercooler_data

def test_intercooler_data_removes_data_from_GET(rf, ic_mw):
    querystring_data = {
        'ic-id': '3',
        'ic-request': 'true',
        'ic-element-id': 'html_id',
        'ic-element-name': 'html_name',
        'ic-target-id': 'target_html_id',
        'ic-trigger-id': 'triggered_by_id',
        'ic-trigger-name': 'triggered_by_html_name',
        'ic-current-url': '/lol/',
        # This is undocumented at the time of writing, and only turns up
        # if no ic-prompt-name is given on the request to inflight.
        'ic-prompt-value': 'undocumented',
        # This may be set if not using
        # <meta name="intercoolerjs:use-actual-http-method" content="true"/>
        '_method': 'POST',
    }
    request = rf.get('/', data=querystring_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    ic_mw.process_request(request)
    assert len(request.GET) == 10
    assert request.intercooler_data.current_url == '/lol/'
    # After evaluation, only _method should be left.
    assert len(request.GET) == 1


def test_http_method_override_via_querystring(rf, http_method_mw):
    request = rf.post('/?_method=patch', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    http_method_mw.process_request(request)
    assert request.changed_method is True
    assert request.method == 'PATCH'
    assert request.original_method == 'POST'


def test_http_method_override_via_header(rf, http_method_mw):
    request = rf.post('/', HTTP_X_HTTP_METHOD_OVERRIDE='patch')
    http_method_mw.process_request(request)
    assert request.changed_method is True
    assert request.method == 'PATCH'
    assert request.original_method == 'POST'


def test_intercooler_querydict_copied_change_method_from_request(rf, http_method_mw, ic_mw):
    request = rf.post('/?_method=patch', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    http_method_mw.process_request(request)
    ic_mw.process_request(request)
    assert request.changed_method is True
    assert request.intercooler_data.changed_method is True
