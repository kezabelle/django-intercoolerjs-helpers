from django.template import engines
from django.views.generic import base as base_views

import pyquery


class ICTemplateResponseMixin(base_views.TemplateResponseMixin):
    @property
    def ic_data(self):
        return self.request.intercooler_data

    def get_target_id(self):
        return self.ic_data.target_id

    def extract_html_part(self, find, from_html):
        '''
        This find the element that has find string then extract the part from
        html string.
        '''
        pq = pyquery.PyQuery(from_html)
        html_part = pq(find).html()
        return html_part

    def render_to_response(self, context, **response_kwargs):
        '''
        This retrieves ic-target-id from ic data, then use it to extract part
        of template which has the id.
        '''
        response = super().render_to_response(context, **response_kwargs)
        if not self.ic_data.request:
            return response

        template_file = response.resolve_template(response.template_name)
        with open(str(template_file.origin)) as tmpl_file:
            tmpl_content = tmpl_file.read()
        html_part = self.extract_html_part(
                '#' + self.get_target_id(), tmpl_content)
        django_engine = engines['django']
        template = django_engine.from_string(html_part)
        response.template_name = template
        return response


class ICDispatchMixin(base_views.View):
    '''
    This provides dispatcher for routing to correct method based on
    IntercoolerJS method/trigger/target tuple.
    '''
    ic_tuples = []

    def dispatch(self, request, *args, **kwargs):
        method = super().dispatch
        if not self.ic_data.request:
            return method(request, *args, **kwargs)
        try:
            req_method = request.method.lower()
            req_trigger = self.ic_data.trigger.id
            req_target = self.ic_data.target_id
            method_name = next(method_name
                    for method, trigger, target, method_name in self.ic_tuples
                    if (not method or method == req_method)
                    and (not trigger or trigger == req_trigger)
                    and (not target or target == req_target)
                    )
            method = getattr(self, method_name)
            # Not catch AttributeError for developer to know what is the wrong
            # method name
        except StopIteration: pass
        return method(request, *args, **kwargs)
