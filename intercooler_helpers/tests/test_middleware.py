# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import pytest
from intercooler_helpers.middleware import IntercoolerMiddleware


@pytest.fixture
def ic_mw():
    return IntercoolerMiddleware()


@pytest.mark.parametrize("method", [
    "maybe_intercooler",
    "is_intercooler",
    "intercooler_data",
])
def test_methods_dont_exist_on_class_only_on_instance(rf, ic_mw, method):
    request = rf.get('/')
    ic_mw.process_request(request)
    assert hasattr(request, method) is True
    assert hasattr(request.__class__, method) is False


def test_maybe_intercooler(rf, ic_mw):
    request = rf.get('/', data={'ic-request': 'true'})
    ic_mw.process_request(request)
    assert request.maybe_intercooler() is True


def test_is_intercooler(rf, ic_mw):
    request = rf.get('/', data={'ic-request': 'true'},
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
    data = request.intercooler_data()
    assert data.current_url == '/lol/'
    assert data.element == ('html_name', 'html_id')
    assert data.id == 3
    assert data.request is True
    assert data.target_id == 'target_html_id'
    assert data.trigger == ('triggered_by_html_name', 'triggered_by_id')
    assert data.prompt_value == 'undocumented'
    assert data._mutable is False
    assert data.changed_method is True
    assert data.dict() == querystring_data

    assert request.changed_method is True
    assert request.method == 'POST'
    assert request.original_method == 'GET'
    # everything else should be consumed into the IC querydict.
    assert set(request.GET.keys()) == {'ic-request', '_method'}
