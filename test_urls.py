# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from uuid import uuid4

from django.conf.urls import url
from django.forms import Form, CharField, IntegerField
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.template.defaultfilters import pluralize
from django.template.response import TemplateResponse
try:
    from django.urls import reverse
except ImportError:  # Django <1.10
    from django.core.urlresolvers import reverse

from intercooler_helpers import views as ic_views


def _page_data():
    return tuple(str(uuid4()) for x in range(0, 10))


clicktrack = 0

def click(request):
    global clicktrack
    clicktrack += 1
    do_reset = (request.is_intercooler() and
                request.intercooler_data.element.id == 'intro-btn2' and
                request.intercooler_data.current_url.match is not None)
    if do_reset:
        clicktrack = 0
    time = pluralize(clicktrack)
    text = "<span>You clicked me {} time{}...</span>".format(clicktrack, time)
    if do_reset:
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

    def save(self): pass


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


def html_part(request, show_details=False):
    template = "demo_project.html"
    context = {
        'show_details': show_details,
    }
    return ic_views.ICTemplateResponse(
            request, template=template, context=context)


class ICView(ic_views.ICTemplateResponseMixin, ic_views.ICDispatchMixin):
    template_name = "demo_project.html"
    ic_tuples = [
            ('get', None, 'test_class', 'get_html_part'),
            ('post', 'post-btn', 'test_class', 'post_message'),
            ('post', 'post-btn', 'target_*', 'post_message'),
            ('get', 'post-btn', None, 'test_full_template'),
            ]
    target_map = {'target_*': 'target_{{ forloop.count }}'}

    def get(self, request, *args, **kwargs):
        context = {'message': 'In GET'}
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return HttpResponse('In POST')

    def get_html_part(self, request, *args, **kwargs):
        context = {
            'message': 'Dispatched to get',
        }
        return self.render_to_response(context)

    def post_message(self, request, *args, **kwargs):
        context = {
            'message': 'Dispatched to post: ' + request.POST['message'],
        }
        return self.render_to_response(context)

    def test_full_template(self, request, *args, **kwargs):
        context = {'message': 'In Full Template'}
        return self.render_to_response(context)


class ICTRNewMap(ic_views.ICTemplateResponse):
    target_map = {'target_id': 'mapped_id'}


class ICUpdate(ic_views.ICTemplateResponseMixin, ic_views.ICDispatchMixin,
        ic_views.ICUpdateView):
    response_class = ICTRNewMap
    template_name = "form.html"

    def check_form(self, request, *args, **kwargs):
        _form = TestForm(request.POST or None)
        return self.form_valid(_form)
        # if self.form_valid(_form):
        #     return redirect(reverse('redirected'))
        # context = {'form': _form}
        # return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return self.check_form(request, *args, **kwargs)


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
    url('^html_part/show/$', html_part, kwargs={'show_details': True},
        name='html_part_show'),
    url('^html_part/$', html_part, kwargs={'show_details': False},
        name='html_part_hide'),
    url('^ic_dispatch/$', ICView.as_view(), name='ic_dispatch'),
    url('^ic_update/$', ICUpdate.as_view(
        ic_tuples=[
            ('get', 'trigger_id', 'target_id', 'action'),
            ('post', 'trigger_id', 'target_id', 'check_form'),
            ],
        target_map={'target_id': 'take_over'},
        ), name='ic_update'),
    url('^$', root, name='root'),
]

