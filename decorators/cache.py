# http://www.djangosnippets.org/snippets/629/
#
def cached(slot_name, timeout=None):
    def decorator(function):
        def invalidate():
            cache.delete(slot_name)

        def wrapped(*args, **kwargs):
            import sys
            result = cache.get(slot_name)
            print >>sys.stderr, 'cached %s : %s' % (slot_name, result)
            if result is None:
                result = function(*args, **kwargs)
                cache.set(slot_name, result, timeout)
            return result
        wrapped.invalidate = invalidate
        return wrapped

    return decorator

# Here is example usage:

#@cached('/data/something_hard')
#def get_something_complex():
#    ....
#    return result

#dispatcher.connect(get_something_complex.invalidate, django.db.models.signals.post_save, Model) 
