from django import template
register = template.Library()

# http://www.djangosnippets.org/snippets/215/

class SetVariable(template.Node):
    def __init__(self,varname,value):
        self.varname = varname
        self.value = value

    def render(self,context):
        var = template.resolve_variable(self.value,context)
        if var:
            context[self.varname] = var
        else:
            context[self.varname] = context[self.value]
        return ''


@register.tag(name='set')
def set_var(parser,token):
    """
    Example:
        {% set category_list category.categories.all %}
        {% set dir_url "../" %}
        {% set type_list "table" %}
        {% include "category_list.html" %}
    """
    from re import split
    bits = split(r'\s+', token.contents, 2)
    return SetVariable(bits[1],bits[2])
