from django.utils.functional import curry
from django.conf.urls.defaults import patterns, url
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.db.models.fields import IntegerField, FieldDoesNotExist
from django.core.exceptions import PermissionDenied

from types import StringTypes

class OrderingField(IntegerField):
    empty_strings_allowed=False
    def __init__(self, with_respect_to=[], **kwargs):
        self.with_respect_to = with_respect_to
        kwargs['null'] = False
        kwargs['editable'] = False
        IntegerField.__init__(self, **kwargs )

    def get_internal_type(self):
        return 'IntegerField'

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if value is None:
            value = model_instance._get_next_order_value()
            setattr(model_instance, self.attname, value)
        return super(OrderingField, self).pre_save(model_instance, add)
        
    def contribute_to_class(self, cls, name):
        assert not hasattr(cls._meta, 'has_ordering_field'), "A model can't have more than one OrderingField."
        super(OrderingField, self).contribute_to_class(cls, name)
        setattr(cls._meta, 'has_ordering_field', True)
        setattr(cls._meta, 'ordering_field', self)
        setattr(cls, 'move_up', curry(cls._move_up_or_down, is_up=True))
        setattr(cls, 'move_down', curry(cls._move_up_or_down, is_up=False))

class Model(object):
    def _get_next_order_value(self):
        field = getattr(self._meta, 'ordering_field')
        try:
            last = self.__class__._default_manager.order_by('-%s' % field.name)[0]
            try:
                last_order = int(getattr(last, field.attname))
            except:
                last_order = 0
            next = last_order + 1
        except IndexError:
            next = 1
        return next
    
    def _move_up_or_down(self, is_up=True):
        field = getattr(self._meta, 'ordering_field')
        with_respect_to = field.with_respect_to
        if type(with_respect_to) == StringTypes:
            with_respect_to = [with_respect_to]
        filter = []
        for fname in with_respect_to:
            f = self._meta.fields[fname]
            filter.append(f.name, getattr(self, f.attname))
        filter.append(('%s%s' % (field.name, is_up and '__lt' or '__gt'), getattr(self, field.attname)))
        order = '%s%s' % (is_up and '-' or '', field.name)
        try:
            a = self.__class__._default_manager.filter(**dict(filter)).order_by(order)[0]
        except IndexError:
            pass
        else:
            a.order, self.order = self.order, a.order
            a.save()
            self.save()

    def reorder(self):
        objs = list(self.__class__.objects.all())
        s = []
        if objs[0] != self:
            s.append('<a href="%s/move/up/">Up</a>' % self.id)
        if objs[-1] != self:
            s.append('<a href="%s/move/down/">Down</a>' % self.id)
        if len(s) > 1:
            s.insert(1, '/')
        return '&nbsp;'.join(s)
    reorder.short_description = 'order'
    reorder.allow_tags = True
    reorder.admin_order_field = 'order'

class SortableModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(SortableModelAdmin, self).get_urls()
        sortable_urls = patterns('',
            (r'^(\d+)/move/(up|down)/$', self.admin_site.admin_view(self.do_reorder))
        )
        return sortable_urls + urls

    def do_reorder(self, request, object_id, direction):
        model = self.model
        opts = model._meta

        try:
            obj = self.queryset(request).get(pk=unquote(object_id))
        except model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if direction == 'up':
            obj.move_up()
        elif direction == 'down':
            obj.move_down()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
