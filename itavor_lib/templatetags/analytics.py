from django.template import Library, Node
from django.conf import settings

register = Library()

@register.inclusion_tag('itavor/google-analytics.html')
def analytics(secure=False):
    """
    Output the google tracker code.
    """
    return({"GOOGLE_CODE": config_value('GOOGLE', 'ANALYTICS_CODE'),
            "secure" : secure})
