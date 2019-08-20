import re

from django import http
from django.core import exceptions
from django.template import engines, response
from django.utils.decorators import classonlymethod
from django.views.generic import base as base_views, edit as edit_views

from lxml import etree


class ICTemplateResponse(response.TemplateResponse):
    '''
    This create response from part or full template, depends on different types
    of target id.

    target_map is in form of {'target_*': 'target_{{ tag }}'}
    '''
    target_map = {}

    @property
    def ic_data(self):
        return self._request.intercooler_data

    def get_target_id(self):
        '''
        This return mapped (if there is any) target id. It tries to use
        matched target id from dispatch. If fail then use target id
        from intercooler data.
        '''
        try:
            target_id = self.ic_data.matched_target
        except AttributeError:
            target_id = self.ic_data.target_id
        try:
            target_id = self.target_map[target_id]
        except KeyError: pass
        return target_id

    @classonlymethod
    def build_xpath(cls, relative='.//*', attrbs={'id': None}):
        '''
        This create xpath using relative path as starting point and attribute dict
        as criteria.
        '''
        # Use sorted to make sure all test times have same result
        criteria = ' and '.join(['@%s="%s"' % (key, value)
            for key, value in sorted(attrbs.items())])
        criteria = ('[%s]' % criteria) if criteria else ''
        return '%s%s' % (relative, criteria)

    def extract_html_part(self, file_name, find=None):
        '''
        This find the element that has find string then extract the part from
        html file.
        '''
        xpath = self.__class__.build_xpath(attrbs={'id': find})
        with open(file_name) as tmpl_file:
            root = etree.fromstring(tmpl_file.read(), etree.HTMLParser())
        # print('extract_html_part', find)
        html_part = None
        # If root is None, something is wrong so developer need to know
        html_part = root.find(xpath)
        # with_tail is to remove django template tag as tail of found html tag
        # FutureWarning: The behavior of this method will change in future
        # versions. Use specific 'len(elem)' or 'elem is not None' test
        # instead.
        # result = html_part or etree.tostring(html_part, with_tail=False)
        result = (None if html_part is None
                else etree.tostring(html_part, with_tail=False))
        # print('"%s"' % result)
        return result

    def resolve_template(self, template):
        '''
        After resolving template, check if request is intercooler and has
        target id. Use the id to extract element which has the id.
        '''
        # super of Python 2.7
        template_obj = super(ICTemplateResponse, self
                ).resolve_template(template)
        # raise Exception('resolve_template %s' % self._request.is_intercooler())
        target_id = self._request.is_intercooler() and self.get_target_id()
        html_part = self.extract_html_part(str(template_obj.origin),
                find=target_id) if target_id else None
        if html_part:
            engine = engines[template_obj.backend.name]
            template_obj = engine.from_string(html_part)
        else: pass
        return template_obj


class ICTemplateResponseMixin(base_views.TemplateResponseMixin):
    target_map = {}
    response_class = ICTemplateResponse

    @property
    def ic_data(self):
        return self.request.intercooler_data

    @classonlymethod
    def prepare_subclass(cls):
        if cls.response_class == ICTemplateResponse: pass
        else:
            return
        cls.response_class = type(
                'ICTR' + cls.__name__, (cls.response_class, ), {})

    @classonlymethod
    def as_view(cls, target_map = {}, **initkwargs):
        cls.prepare_subclass()
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
            esc_first = re.escape(first).replace(r'\*', '.*')
            # print('%r <> %r' % (esc_first, second))
            return re.match(esc_first, str(second))
        try:
            target, method_name = next((target, method_name)
                    for method, trigger, target, method_name in self.ic_tuples
                    if match(method, req_method)
                    and match(trigger, req_trigger)
                    and match(target, req_target)
                    )
            method = getattr(self, method_name)
            self.ic_data.matched_target = target
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
