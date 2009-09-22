from django.template import loader, RequestContext
from django.http import HttpResponse
from django.core.paginator import Paginator, InvalidPage
from django.conf import settings

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

__all__ = ('render_to', 'render_paginated_to')
