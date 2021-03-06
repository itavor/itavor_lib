from django import forms
from django.forms import widgets
from django.conf import settings
from django.template.defaulttags import mark_safe
from django.contrib.auth.models import User
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.text import truncate_words
from django.utils.translation import ugettext as _

from PIL import Image
import os

class AutoCompleteWidget(widgets.MultiWidget):

    CLIENT_CODE = """
    <script type="text/javascript">
    $('document').ready(function () {
        $('#id_%s_1').autocomplete('/admin/autocomplete/', {
         'hidden_input': $('#id_%s_0')
        });
    });
    </script>
    """

    def __init__(self, attrs=None):
        widget_list = (widgets.HiddenInput(attrs=attrs), widgets.TextInput(attrs=attrs))
        super(AutoCompleteWidget, self).__init__(widget_list, attrs)

    def decompress(self, value):
        """
        Accepts a single value which it then extracts enough values to
        populate the various widgets.
        
        We'll provide the id for the hidden input and a user
        representable string for the shown input field.
        """
        if value:
            obj = User.objects.get(id=value)
            return [obj.id, str(obj)]
        return [None, None]

    def render(self, name, value, attrs=None):
        """
        Converts the widget to an html representation of itself.
        """
        output = super(AutoCompleteWidget, self).render(name, value, attrs)
        return output + mark_safe(self.CLIENT_CODE % (name, name))

    class Media:
        css = {'all': (settings.MEDIA_URL + '/admin/css/jquery.autocomplete.css',)}
        js = (settings.MEDIA_URL + 'admin/js/jquery-1.3.2.js',
              settings.MEDIA_URL + 'admin/js/jquery.autocomplete.js')

class ForeignKeySearchInput(forms.HiddenInput):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a <select> box.
    """
    class Media:
        css = {
            'all': ('css/jquery.autocomplete.css',)
        }
        js = (
            'js/jquery.js',
            'js/jquery.bgiframe.pack.js',
            'js/jquery.ajaxQueue.js',
            'js/jquery.autocomplete.pack.js'
        )

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        return truncate_words(obj, 14)

    def __init__(self, rel, search_fields, attrs=None):
        self.rel = rel
        self.search_fields = search_fields
        super(ForeignKeySearchInput, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        rendered = super(ForeignKeySearchInput, self).render(name, value, attrs)
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        return rendered + mark_safe(u'''
            <style type="text/css" media="screen">
                #lookup_%(name)s {
                    padding-right:16px;
                    background: url(
                        %(admin_media_prefix)simg/admin/selector-search.gif
                    ) no-repeat right;
                }
                #del_%(name)s {
                    display: none;
                }
            </style>
<input type="text" id="lookup_%(name)s" value="%(label)s" />
<a href="#" id="del_%(name)s">
<img src="%(admin_media_prefix)simg/admin/icon_deletelink.gif" />
</a>
<script type="text/javascript">
            if ($('#lookup_%(name)s').val()) {
                $('#del_%(name)s').show()
            }
            $('#lookup_%(name)s').autocomplete('../search/', {
                extraParams: {
                    search_fields: '%(search_fields)s',
                    app_label: '%(app_label)s',
                    model_name: '%(model_name)s',
                },
            }).result(function(event, data, formatted) {
                if (data) {
                    $('#id_%(name)s').val(data[1]);
                    $('#del_%(name)s').show();
                }
            });
            $('#del_%(name)s').click(function(ele, event) {
                $('#id_%(name)s').val('');
                $('#del_%(name)s').hide();
                $('#lookup_%(name)s').val('');
            });
            </script>
        ''') % {
            'search_fields': ','.join(self.search_fields),
            'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
            'model_name': self.rel.to._meta.module_name,
            'app_label': self.rel.to._meta.app_label,
            'label': label,
            'name': name,
        }

try:
    from sorl.thumbnail.main import DjangoThumbnail
    def thumbnail(image_path):
        t = DjangoThumbnail(relative_source=image_path, requested_size=(200, 200))
        return u'<img src="%s" alt="%s" />' % (t.absolute_url, image_path)
except ImportError:
    def thumbnail(image_path):
        absolute_url = os.path.join(settings.MEDIA_ROOT, image_path)
        return u'<img src="%s" alt="%s" />' % (absolute_url, image_path)

class AdminImageWidget(AdminFileWidget):
    """
    A FileField Widget that displays an image instead of a file path
    if the current file is an image.
    """
    def render(self, name, value, attrs=None):
        output = []
        file_name = str(value)
        if file_name:
            file_path = '%s%s' % (settings.MEDIA_URL, file_name)
            try:            # is image
                Image.open(os.path.join(settings.MEDIA_ROOT, file_name))
                output.append('<a target="_blank" href="%s">%s</a><br />%s <a target="_blank" href="%s">%s</a><br />%s ' % \
                    (file_path, thumbnail(file_name), _('Currently:'), file_path, file_name, _('Change:')))
            except IOError: # not image
                output.append('%s <a target="_blank" href="%s">%s</a> <br />%s ' % \
                    (_('Currently:'), file_path, file_name, _('Change:')))
            
        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe('<div style="margin-left: 110px">%s</div>' % u''.join(output))
