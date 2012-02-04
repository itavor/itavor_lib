from django.db import models
from django.template import loader, RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.paginator import Paginator, InvalidPage
from django.conf import settings
from django.utils import simplejson as json
from django.core.serializers.json import DateTimeAwareJSONEncoder

import time
import datetime
import types
from decimal import *

# django_template based on http://www.djangosnippets.org/snippets/596/

decorator_with_args = lambda decorator: lambda *args, **kwargs: lambda func: decorator(func, *args, **kwargs )

templates = {}

def django_template_to_string(request, variables, template):
    """
    usage:
      
    django_template_to_string(request, { 'title' : 'hello' }, "base.html")
    """
    cached = 'Template not cached'
    if not settings.DEBUG:
        temp = templates.get(template)
        cached = 'Template cached'
        if temp is None:
            temp = loader.get_template(template)
            templates[template] = temp

    else:
        temp = loader.get_template(template)

    c = RequestContext(request)
    c.update(variables)
    c['cached'] = cached
    return temp.render(c)

@decorator_with_args
def render_to(func, template=None):
    """
    usage:

    @render_to("moja_strona.html")
    def master_home(request):
        variables = { 'title' : "Hello World!" }
        return variables
    """
    def wrapper(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        if isinstance(response, HttpResponse):
            return response
        string = django_template_to_string(request, response, template)
        return HttpResponse(string)
        
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper

@decorator_with_args
def render_paginated_to(func, template=None):
    """
    A conversion of django.views.generic.object_list to a decorator

    usage:

    @render_paginated_to("moja_strona.html")
    def master_home(request):
        variables = {
             'object_list': items,
             'allow_empty': True,
             'paginate_by': 5 }
        return variables
    """
    def wrapper(request, *args, **kwargs):
        page = kwargs.pop('page', None)
        variables = func(request, *args, **kwargs)

        object_list = variables['object_list']
        paginate_by = variables.get('paginate_by', 10)

        paginator = Paginator(object_list, paginate_by)
        if not page:
            page = request.GET.get('page', 1)
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.pages
            else:
                # Page is not 'last', nor can it be converted to an int
                raise Http404
    
        try:
            object_list = paginator.get_page(page_number - 1)
        except InvalidPage:
            if page_number == 1 and allow_empty:
                object_list = []
            else:
                raise Http404

        variables.update({
            'object_list': object_list,
            'paginate_by': paginate_by,
            'page': page,
            'is_paginated': paginator.pages > 1,
            'results_per_page': paginate_by,
            'has_next': paginator.has_next_page(page_number - 1),
            'has_previous': paginator.has_previous_page(page_number - 1),
            'page': page_number,
            'next': page_number + 1,
            'previous': page_number - 1,
            'last_on_page': paginator.last_on_page(page_number - 1),
            'first_on_page': paginator.first_on_page(page_number - 1),
            'pages': paginator.pages,
            'hits' : paginator.hits,
            'page_range' : paginator.page_range
            })
        string = django_template_to_string(request, variables, template)
        return HttpResponse(string)
        
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper

# 'render' based on http://www.djangosnippets.org/snippets/1733/

class render:
    '''Register response engines based on HTTP_ACCEPT
     
     parameters:
         template: template for html rendering
         format: supported formats ('json','html')
         
     @render('index.html')
     def my_view(request)

     @render('index.html', ('json',))
     def my_view(request)
          
    html format is supported by default if a template is defined.
    
     @render('json')
     def my_view(request)
    
    in above case, json is the default format.
    
    '''
    class render_decorator:
        
        def __init__(self, parent, view_func):
            self.parent = parent
            self.view_func = view_func
        
        def __call__(self, *args, **kwargs):
            request = args[0]    
            context = self.view_func(*args, **kwargs)

            if isinstance(context, HttpResponse):
                return context
            
            engine = None
            
            if request.META.has_key('HTTP_ACCEPT'):
                accept = request.META['HTTP_ACCEPT']
                for content in self.parent.engines.iterkeys():
                    if accept.find(content) <> -1:
                        engine, template = self.parent.engines.get(content) 
                        break
            
            if engine is None:
                engine, template = self.parent.engines.get(self.parent.default)
            
            cook = context.pop('cookjar',None)

            if 'html' == engine:
                response = self.html_render(request, context, template)
            elif 'json' == engine:
                response = self.json_render(request, context)
            else:
                response = context

            if isinstance(response, HttpResponse):
                if cook:
                    for k,v in cook.iteritems():
                        if v is None:
                            response.delete_cookie(str(k))
                        else:
                            response.set_cookie(str(k), str(v), getattr(settings, 'COMMON_COOKIE_AGE', None))

            return response
            
        def json_render(self,request, context):
            return render_to_json(context)
        
        def html_render(self,request, context, template):
            return render_to_response(
                template, 
                context, 
                context_instance=RequestContext(request),
            )            
    
    def __register_engine(self, engine, template, default = False):
        
        if engine == 'json':
            content_type = 'application/json'
        elif engine == 'html':
            content_type = 'text/html'
        else:
            raise ValueError("Unsuported format %s" % engine)
        
        if default:
            self.default = content_type
        self.engines[content_type] = engine, template
        
    def __init__(self, template=None, format=None):

        self.engines = {}
        
        if format is None:
            format = ()
        elif not isinstance(format, tuple):
            format = (format,)

        if template == 'json':
            self.__register_engine('json', None, True)
        elif template:
            self.__register_engine('html', template, True)
            
        for f in format:
            self.__register_engine(f, None)
            
    def __call__(self, view_func):
        return render.render_decorator(self, view_func)

def render_to_json(context):
    resp = []
    for k in context.iterkeys():
        resp.append('"%s": %s' % (k, parse(context[k])))
    data = '{%s}' % ','.join(resp)
    return HttpResponse(data, mimetype='application/json')    
    
def parse(data):
    """
    The main issues with django's default json serializer is that properties that
    had been added to a object dynamically are being ignored (and it also has 
    problems with some models).
    """

    def _any(data):
        ret = None
        if type(data) is types.ListType:
            ret = _list(data)
        elif type(data) is types.DictType:
            ret = _dict(data)
        elif isinstance(data, Decimal):
            # json.dumps() cant handle Decimal
            #ret = str(data)
            ret = float(data)
        elif isinstance(data, models.query.QuerySet):
            # Actually its the same as a list ...
            ret = _list(data)
        elif isinstance(data, models.Model):
            ret = _model(data)
        elif isinstance(data, datetime.date):
            ret = time.strftime("%Y/%m/%d",data.timetuple())
        else:
            ret = data
        return ret
    
    def _model(data):
        ret = {}
        # If we only have a model, we only want to encode the fields.
        for f in data._meta.fields:
            ret[f.attname] = _any(getattr(data, f.attname))
        # And additionally encode arbitrary properties that had been added.
        fields = dir(data.__class__) + ret.keys()
        add_ons = [k for k in dir(data) if k not in fields]
        for k in add_ons:
            ret[k] = _any(getattr(data, k))
        return ret
    
    def _list(data):
        ret = []
        for v in data:
            ret.append(_any(v))
        return ret
    
    def _dict(data):
        ret = {}
        for k,v in data.items():
            ret[k] = _any(v)
        return ret
    
    ret = _any(data)
    
    return json.dumps(ret, cls=DateTimeAwareJSONEncoder)

__all__ = ('render_to', 'render_paginated_to', 'render')
