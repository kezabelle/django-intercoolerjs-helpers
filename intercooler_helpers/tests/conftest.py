# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pytest

from intercooler_helpers.middleware import IntercoolerData, HttpMethodOverride


@pytest.fixture
def ic_mw():
    return IntercoolerData()


@pytest.fixture
def http_method_mw():
    return HttpMethodOverride()


@pytest.fixture
def ic_req(rf, ic_mw):
    def make_request(**kwargs):
        request = rf.get('/',
                         HTTP_X_IC_REQUEST="true",
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest', **kwargs)
        ic_mw.process_request(request)
        return request
    return make_request
