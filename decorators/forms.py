from django.http import HttpResponse

def post_required(func):
    """Decorator that returns an error unless request.method == 'POST'."""
    def post_wrapper(request, *args, **kwds):
        if request.method != 'POST':
            return HttpResponse('This requires a POST request.', status=405)
        return func(request, *args, **kwds)

    post_wrapper.__name__ = func.__name__
    return post_wrapper
