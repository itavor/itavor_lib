from django.http import HttpResponse
from django.utils import simplejson
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _

import sys

def json_view(func):
    def wrap(request, *a, **kw):
        response = None
        try:
            response = func(request, *a, **kw)
            assert isinstance(response, dict)
            if 'result' not in response:
                response['result'] = 'ok'
        except KeyboardInterrupt:
            # Allow keyboard interrupts through for debugging.
            raise
        except Exception, e:
            # Mail the admins with the error
            exc_info = sys.exc_info()
            subject = 'JSON view error: %s' % request.path
            try:
                request_repr = repr(request)
            except:
                request_repr = 'Request repr() unavailable'
            import traceback
            message = 'Traceback:\n%s\n\nRequest:\n%s' % (
                '\n'.join(traceback.format_exception(*exc_info)),
                request_repr,
                )
            mail_admins(subject, message, fail_silently=True)

            # Come what may, we're returning JSON.
            if hasattr(e, 'message'):
                msg = e.message
            else:
                msg = _('Internal error') + ': ' + str(e)
            response = {'result': 'error',
                        'text': msg}

        cookies = []
        if 'cookies' in response:
            cookies = response['cookies']
            del response['cookies']

        json = simplejson.dumps(response)
        http_response = HttpResponse(json, mimetype='application/json')
        
        for cookie in cookies:
            http_response.set_cookie(**cookie)
        return http_response

    wrap.__name__ = func.__name__
    wrap.__dict__ = func.__dict__
    wrap.__doc__ = func.__doc__
    return wrap

__all__ = ('json_view',)
