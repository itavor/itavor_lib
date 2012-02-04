from django import template

import datetime

register = template.Library()

@register.simple_tag
def copyright_since(since):
    now = datetime.datetime.now().year
    if since != now:
        return u'&copy; %d&#151;%d' % (int(since), now)
    return u'&copy; %d' % now
