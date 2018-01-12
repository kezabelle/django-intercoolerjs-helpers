# -*- coding: utf-8 -*-
from __future__ import (absolute_import, print_function, unicode_literals,
                        division, )

import inspect

import pytest
from django.forms import Form, IntegerField
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic.base import View

from intercooler_helpers.decorators import (ic_select_from_response,
                                            ic_redirect)
from intercooler_helpers.helpers import CAN_PYQUERY

skip_missing_pyquery_lxml =  pytest.mark.skipif(
    CAN_PYQUERY is False,
    reason="Test execution depends on PyQuery and lxml packages"
)


def _select_from_response_fbv(request, pk):
    class TestForm(Form):
        number = IntegerField(max_value=10, min_value=5)
    context = {'form': TestForm(request.GET or None)}
    return TemplateResponse(request, template="form.html", context=context).render()

class _select_from_response_cbv(View):
    def get(self, request, pk):
        return _select_from_response_fbv(request, pk)

@ic_select_from_response
def select_from_response_view(request, pk):
    return _select_from_response_fbv(request, pk)

@ic_select_from_response()
def select_from_response_view2(request, pk):
    return _select_from_response_fbv(request, pk)


@method_decorator(ic_select_from_response, name='dispatch')
class SelectFromResponseView(_select_from_response_cbv):
    pass

class SelectFromResponseView2(_select_from_response_cbv):
    @method_decorator(ic_select_from_response)
    def dispatch(self, *args, **kwargs):
        return super(SelectFromResponseView2, self).dispatch(*args, **kwargs)

@skip_missing_pyquery_lxml
@pytest.mark.parametrize("view", [
    select_from_response_view,
    select_from_response_view2,
    ic_select_from_response(_select_from_response_cbv.as_view()),
    SelectFromResponseView.as_view(),
    SelectFromResponseView2.as_view(),
])
def test_select_from_response(ic_req, view):
    request = ic_req(data={'ic-select-from-response': '#example-form:first'})
    response = view(request, 11)
    assert response.content.startswith(b'<form action="/form/"') is True

@pytest.mark.parametrize("view,spec,name", [
    (_select_from_response_fbv, ['request', 'pk'], '_select_from_response_fbv'),
    (select_from_response_view, ['request', 'pk'], 'select_from_response_view'),
    (select_from_response_view2, ['request', 'pk'], 'select_from_response_view2'),
])
def test_select_from_response_argspec(view, spec, name):
    argspec = inspect.getargspec(view)
    assert argspec.args == spec
    assert view.__name__ == name

# =============================================================================

def _redirect_fbv(request, pk):
    resp = HttpResponseRedirect('/wheee/')
    resp['Custom1'] = '1'
    resp['Custom2'] = '1'
    return resp


class _redirect_cbv(View):
    def get(self, request, pk):
        return _redirect_fbv(request, pk)

@ic_redirect
def redirect_view(request, pk):
    return _redirect_fbv(request, pk)

@ic_redirect()
def redirect_view2(request, pk):
    return _redirect_fbv(request, pk)

@ic_redirect(keep_headers=['Custom1'])
def redirect_view3(request, pk):
    return _redirect_fbv(request, pk)

@method_decorator(ic_redirect, name='dispatch')
class RedirectView(_redirect_cbv):
    pass

@method_decorator(ic_redirect(), name='dispatch')
class RedirectView2(_redirect_cbv):
    pass

@method_decorator(ic_redirect(keep_headers=['Custom1']), name='dispatch')
class RedirectView3(_redirect_cbv):
    pass

class RedirectView4(_redirect_cbv):
    @method_decorator(ic_redirect)
    def dispatch(self, *args, **kwargs):
        return super(RedirectView4, self).dispatch(*args, **kwargs)

class RedirectView5(_redirect_cbv):
    @method_decorator(ic_redirect())
    def dispatch(self, *args, **kwargs):
        return super(RedirectView5, self).dispatch(*args, **kwargs)

class RedirectView6(_redirect_cbv):
    @method_decorator(ic_redirect(keep_headers=['Custom1']))
    def dispatch(self, *args, **kwargs):
        return super(RedirectView6, self).dispatch(*args, **kwargs)


@pytest.mark.parametrize("view", [
    redirect_view,
    redirect_view2,
    redirect_view3,
    ic_redirect(_redirect_cbv.as_view()),
    RedirectView.as_view(),
    RedirectView2.as_view(),
    RedirectView3.as_view(),
    RedirectView4.as_view(),
    RedirectView5.as_view(),
    RedirectView6.as_view(),
])
def test_redirect(ic_req, view):
    request = ic_req()
    response = view(request, 1)
    assert response.status_code == 200
    assert response.has_header('X-IC-Redirect') is True
    assert response['X-IC-Redirect'] == '/wheee/'


@pytest.mark.parametrize("view,spec,name", [
    (_redirect_fbv, ['request', 'pk'], '_redirect_fbv'),
    (redirect_view, ['request', 'pk'], 'redirect_view'),
    (redirect_view2, ['request', 'pk'], 'redirect_view2'),
    (redirect_view3, ['request', 'pk'], 'redirect_view3'),
])
def test_redirect_argspec(view, spec, name):
    argspec = inspect.getargspec(view)
    assert argspec.args == spec
    assert view.__name__ == name

@pytest.mark.parametrize("view", [
    ic_redirect(_redirect_fbv, keep_headers=['Custom1']),
    ic_redirect(_redirect_cbv.as_view(), keep_headers=['Custom1']),
])
def test_redirect_keeping_only_some_headers(ic_req, view):
    request = ic_req()
    response = view(request, 12)
    assert response.status_code == 200
    assert response.has_header('Custom1') is True
    assert response.has_header('Custom2') is False
    assert response['X-IC-Redirect'] == '/wheee/'

# =============================================================================

#
# def _push(request):
#     return HttpResponse(b'test')
#
# @ic_push_url(lambda request: 'lol')
# def push_fbv(request):
#     return _push(request)
#
# class _push_cbv(View):
#     def get(self, request):
#         return _push(request)
#
#
# @method_decorator(ic_push_url(lambda request: 'lol'), name='dispatch')
# class PushView(_push_cbv):
#     pass
#
#
# class PushView2(_push_cbv):
#     @method_decorator(ic_push_url(lambda request: 'lol'))
#     def dispatch(self, *args, **kwargs):
#         return super(PushView2, self).dispatch(*args, **kwargs)
#
#
# @pytest.mark.parametrize("view", [
#     push_fbv,
#     PushView.as_view(),
#     PushView2.as_view(),
# ])
# def test_push_url(ic_req, view):
#     request = ic_req()
#     response = view(request)
#     assert response['X-IC-PushURL'] == '/'
#     assert response.content == b'test'
