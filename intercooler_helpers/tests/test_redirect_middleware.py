# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pytest
from django.http import HttpResponse
from django.shortcuts import redirect

from intercooler_helpers.middleware import IntercoolerRedirector, \
    IntercoolerData


@pytest.mark.parametrize("response", [
    redirect('/test/', permanent=False),
    redirect('/', permanent=True),
])
def test_redirects_turn_into_clientside_redirects(rf, response):
    request = rf.get('/', HTTP_X_IC_REQUEST="true",
                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    IntercoolerData().process_request(request)
    url = response.url
    changed_response = IntercoolerRedirector().process_response(request, response)
    assert changed_response.has_header('X-IC-Redirect') is True
    assert changed_response.has_header('Location') is False
    assert changed_response['X-IC-Redirect'] == url


@pytest.mark.parametrize("response", [
    HttpResponse(status=201),
    HttpResponse(status=307),
    HttpResponse(status=501),
])
def test_redirects_not_applied_for_non_redirection_statuscodes(rf, response):
    request = rf.get('/', HTTP_X_IC_REQUEST="true",
                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    IntercoolerData().process_request(request)
    changed_response = IntercoolerRedirector().process_response(request, response)
    assert changed_response.has_header('X-IC-Redirect') is False


def test_redirect_dies_without_intercoolerdata_middleware(rf):
    request = rf.get('/')
    response = HttpResponse(status=201)
    with pytest.raises(AttributeError) as exc:
        IntercoolerRedirector().process_response(request, response)

