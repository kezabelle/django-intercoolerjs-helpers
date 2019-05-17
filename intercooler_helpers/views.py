from django.template import engines, response
from django.views.generic import base as base_views

import pyquery


class ICTemplateResponse(response.TemplateResponse):
    @property
    def ic_data(self):
        return self._request.intercooler_data

    def get_target_id(self):
        return self.ic_data.target_id

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
        template_obj = super().resolve_template(template)
        if self._request.is_intercooler() and self.get_target_id(): pass
        else:
            return template_obj

        html_part = self.extract_html_part(
                str(template_obj.origin), '#' + self.get_target_id())
        engine = engines[template_obj.backend.name]
        template_obj = engine.from_string(html_part)
        return template_obj


class ICTemplateResponseMixin(base_views.TemplateResponseMixin):
    response_class = ICTemplateResponse

    @property
    def ic_data(self):
        return self.request.intercooler_data


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
