# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import urls
from django.core import exceptions
import pytest

from intercooler_helpers import views


def test_get_without_ic(client):
    response = client.get(urls.reverse('ic_dispatch'))
    # print(response, '\n', *dir(response), sep='\t')
    assert 'In GET' in response.content.decode('utf-8')

def test_post_without_ic(client):
    response = client.post(urls.reverse('ic_dispatch'))
    assert response.content.decode('utf-8') == 'In POST'

@pytest.mark.parametrize('pair', [
    ({'id': 'test'}, './/*[@id="test"]'),
    ({'id': 'test', 'name': 'test_name'},
        './/*[@id="test" and @name="test_name"]'),
    ])
def test_build_xpath(pair):
    xpath = views.ICTemplateResponse.build_xpath(attrbs=pair[0])
    assert xpath == pair[1]

@pytest.mark.parametrize('target_id', ['test_class', 'target_1', 'target_2'])
def test_post_ic_get_html_part(client, target_id):
    data = {
            'ic-request': 'true',
            'ic-trigger-id': 'post-btn',
            'ic-target-id': target_id,
            'message': 'message',
            }
    response = client.post(urls.reverse('ic_dispatch'), data=data,
            HTTP_X_IC_REQUEST="true", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    content = response.content.decode('utf-8')
    assert 'Dispatched to post: %s' % data['message'] in content
    # No other html tag than the message one
    assert '<a id="post-btn"' not in content

def test_get_ic_not_match_target(client):
    data = {
            'ic-request': 'true',
            'ic-target-id': 'not_exist',
            }
    response = client.get(urls.reverse('ic_dispatch'), data=data,
            HTTP_X_IC_REQUEST="true", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    content = response.content.decode('utf-8')
    assert 'In GET' in content

def test_get_ic_without_target_id_has_full_template(client):
    data = {
            'ic-request': 'true',
            'ic-trigger-id': 'post-btn',
            }
    response = client.get(urls.reverse('ic_dispatch'), data=data,
            HTTP_X_IC_REQUEST="true", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    content = response.content.decode('utf-8')
    # To make sure the test_full_template is called
    assert 'Full Template' in content
    assert '<a id="post-btn"' in content

def test_no_method_raise_error(client):
    data = {
            'ic-request': 'true',
            'ic-trigger-id': 'trigger_id',
            'ic-target-id': 'target_id',
            }
    error = None
    try:
        response = client.get(urls.reverse('ic_update'), data=data,
                HTTP_X_IC_REQUEST="true",
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    except AttributeError as e:
        error = e
    assert error

def test_post_ic_for_form_valid(client):
    data = {
            'ic-request': 'true',
            'ic-trigger-id': 'trigger_id',
            'ic-target-id': 'target_id',
            'field': 'test',
            'number': 5,
            }
    response = client.post(urls.reverse('ic_update'), data=data,
            HTTP_X_IC_REQUEST="true", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    content = response.content.decode('utf-8')
    assert 'id="example-form"' in content

def test_post_without_ic_for_form_valid(client):
    data = {
            'field': 'test',
            'number': 5,
            }
    error = None
    try:
        response = client.post(urls.reverse('ic_update'), data=data)
    except exceptions.ImproperlyConfigured as e:
        error = e
    assert error
