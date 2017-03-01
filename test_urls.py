# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import threading
from uuid import uuid4

from django.conf.urls import url
from django.forms import Form, CharField, IntegerField
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.template.defaultfilters import pluralize
from django.template.response import TemplateResponse
from django.urls import reverse


def _page_data():
    return tuple(str(uuid4()) for x in range(0, 10))


clicktrack = 0

def click(request):
    global clicktrack
    clicktrack += 1
    if request.method == "GET":
        clicktrack = 0
    time = pluralize(clicktrack)
    text = "<span>You clicked me {} time{}...</span>".format(clicktrack, time)
    if request.method == "GET":
        text = "<span>You reset the counter!, via {}</span>".format(request.intercooler_data.trigger.id)
    if not request.is_intercooler():
        raise Http404("Not allowed to come here outside of an Intercooler.js request!")
    resp = HttpResponse(text)
    return resp


def redirector(request):
    return redirect(reverse('redirected'))


def redirected(request):
    return TemplateResponse(request, template="redirected.html", context={})


class TestForm(Form):
    field = CharField()
    number = IntegerField(max_value=10, min_value=5)


def form(request):
    template = "form.html"
    _form = TestForm(request.POST or None)
    if _form.is_valid():
        return redirect(reverse('redirected'))
    context = {'form': _form}
    return TemplateResponse(request, template=template, context=context)



def polling_stop(request):
    resp = HttpResponse("Cancelled")
    resp['X-IC-CancelPolling'] = "true"
    return resp


def polling_start(request):
    resp = HttpResponse("")
    resp['X-IC-ResumePolling'] = "true"
    return resp


def polling(request):
    template = "polling.html"
    if request.is_intercooler():
        template = "polling_response.html"
    context = {
        'item': str(uuid4()),
    }
    return TemplateResponse(request, template=template, context=context)


def infinite_scrolling(request):
    template = "infinite_scrolling.html"
    if request.is_intercooler():
        template = "infinite_scrolling_include.html"
    context = {
        'rows': _page_data(),
    }
    return TemplateResponse(request, template=template, context=context)


def root(request):
    template = "demo_project.html"
    context = {
        'rows': _page_data(),
        'form': TestForm()
    }
    return TemplateResponse(request, template=template, context=context)


urlpatterns = [
    url('^form/$', form, name='form'),
    url('^redirector/redirected/$', redirected, name='redirected'),
    url('^redirector/$', redirector, name='redirector'),
    url('^click/$', click, name='click'),
    url('^polling/stop/$', polling_stop, name='polling_stop'),
    url('^polling/start/$', polling_start, name='polling_start'),
    url('^polling/$', polling, name='polling'),
    url('^infinite/scrolling/$', infinite_scrolling, name='infinite_scrolling'),
    url('^$', root, name='root'),
]

