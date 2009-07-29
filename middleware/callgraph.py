import time
import pycallgraph
from django.conf import settings

class CallgraphMiddleware(object):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and 'graph' in request.GET:
            filter_func = pycallgraph.GlobbingFilter(include=['*'],
                    exclude=['debug_toolbar.*', '*.debug.*'])
            pycallgraph.start_trace(filter_func=filter_func)

    def process_response(self, request, response):
        if settings.DEBUG and 'graph' in request.GET:
            pycallgraph.make_dot_graph('callgraph-' + str(time.time()) + '.png')
        return response

