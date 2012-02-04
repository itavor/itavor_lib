from django import template
from django.utils.safestring import SafeUnicode

import re

register = template.Library()

@register.filter("encode_email")
def encode_email(value):
    return do_encode_email(value)

def do_encode_email(value):
    emails = []
    mailsrch = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
    emails = mailsrch.findall(value)

    encoded = dict([ (e, _encode(e)) for e in emails ])
    for orig, encoded in encoded.items():
        value = value.replace(orig, encoded)
    return SafeUnicode(value)

def _encode(email):
    return ''.join([ '&#%s;' % str(ord(a)) for a in email ])
