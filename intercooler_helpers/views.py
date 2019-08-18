import re

from django import http
from django.core import exceptions
from django.template import engines, response
from django.utils.decorators import classonlymethod
from django.views.generic import base as base_views, edit as edit_views

import pyquery


class ICTemplateResponse(response.TemplateResponse):
    target_map = {}

    @property
    def ic_data(self):
        return self._request.intercooler_data

    def get_target_id(self):
        target_id = self.ic_data.target_id
        try:
            return self.target_map[target_id]
        except KeyError: pass
        return target_id

    def extract_html_part(self, file_name, find):
        '''
        This find the element that has find string then extract the part from
        html file.
        '''
        with open(file_name) as tmpl_file:
            tmpl_content = tmpl_file.read()
        pq = pyquery.PyQuery(tmpl_content)
        html_part = pq(find).html()
        return html_part

    def resolve_template(self, template):
        '''
        After resolving template, check if request is intercooler and has
        target id. Use the id to extract element which has the id.
        '''
        # super of Python 2.7
        template_obj = super(ICTemplateResponse, self
                ).resolve_template(template)
        target_id = self._request.is_intercooler() and self.get_target_id()
        if target_id: pass
        else:
            return template_obj

        html_part = self.extract_html_part(
                str(template_obj.origin), '#' + target_id)
        engine = engines[template_obj.backend.name]
        template_obj = engine.from_string(html_part)
        return template_obj


class ICTemplateResponseMixin(base_views.TemplateResponseMixin):
    target_map = {}
    response_class = ICTemplateResponse

    @property
    def ic_data(self):
        return self.request.intercooler_data

    @classonlymethod
    def as_view(cls, target_map = {}, **initkwargs):
        cls.response_class.target_map = target_map or cls.target_map
        # super of Python 2.7
        return super(ICTemplateResponseMixin, cls).as_view(**initkwargs)


class ICDispatchMixin(base_views.View):
    '''
    This provides dispatcher for routing to correct method based on
    IntercoolerJS method/trigger/target tuple.
    '''
    @classonlymethod
    def as_view(cls, ic_tuples = [], **initkwargs):
        if ic_tuples:
            cls.ic_tuples = ic_tuples
        else: pass
        # super of Python 2.7
        return super(ICDispatchMixin, cls).as_view(**initkwargs)

    def dispatch(self, request, *args, **kwargs):
        # super of Python 2.7
        method = super(ICDispatchMixin, self).dispatch
        if not self.ic_data.request:
            return method(request, *args, **kwargs)
        req_method = request.method.lower()
        req_trigger = self.ic_data.trigger.id
        req_target = self.ic_data.target_id
        # print('dispatch', request.POST, req_method, req_trigger, req_target)
        # print(self.ic_tuples)
        def match(first, second):
            if not first or first == second:
                return True
            esc_first = re.escape(first).replace('\\*', '.*')
            # print('%r <> %r' % (esc_first, second))
            return re.match(esc_first, str(second))
        try:
            method_name = next(method_name
                    for method, trigger, target, method_name in self.ic_tuples
                    if match(method, req_method)
                    and match(trigger, req_trigger)
                    and match(target, req_target)
                    )
            method = getattr(self, method_name)
            # Not catch AttributeError for developer to know what is the wrong
            # method name
        except StopIteration: pass
        # Explicit is better than implicit
        # return http.HttpResponseServerError(
        #         '%s: Not implemented method %s, trigger %s, target %s'
        #         % (self.__class__.__name__,
        #             req_method, req_trigger, req_target))
        return method(request, *args, **kwargs)


class ICUpdateView(edit_views.UpdateView):
    def form_valid(self, form):
        if self.ic_data.request: pass
        else:
            try:
                # super of Python 2.7
                return super(ICUpdateView, self).form_valid(form)
            except exceptions.ImproperlyConfigured as err:
                message = err.args[0].replace(
                        'a url',
                        'a url or define a get_success_url method in view class')
                raise exceptions.ImproperlyConfigured(message)
        self.object = form.save()
        # Although the form is valid, as user cannot refresh ic post
        # request, we reuse form_invalid logic to render neccessary
        # template.
        # super of Python 2.7
        return super(ICUpdateView, self).form_invalid(form)
