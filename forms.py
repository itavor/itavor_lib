from django import forms
from django.forms.forms import BoundField
from django.template import Context, loader

class TemplatedForm(forms.Form):
    template = 'forms/form.html'

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('template'):
            self.template = kwargs['template']
            unset(kwargs['template'])
        super(TemplatedForm, self).__init__(*args, **kwargs)

    def output_via_template(self):
        "Helper function for fieldsting fields data from form."
        bound_fields = [BoundField(self, field, name) for name, field \
                        in self.fields.items()]
        bound_fields_dict = dict([(a.name, a) for a in bound_fields])
        c = Context({
            'form': self,
            'bound_fields': bound_fields,
            'bound_fields_dict':bound_fields_dict
        })
        t = loader.get_template(self.template)
        return t.render(c)
        
    def __unicode__(self):
        return self.output_via_template()

class TemplatedModelForm(forms.ModelForm):
    template = 'forms/form.html'

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('template'):
            self.template = kwargs['template']
            unset(kwargs['template'])
        super(TemplatedModelForm, self).__init__(*args, **kwargs)

    def output_via_template(self):
        "Helper function for fieldsting fields data from form."
        bound_fields = [BoundField(self, field, name) for name, field \
                        in self.fields.items()]
        bound_fields_dict = dict([(a.name, a) for a in bound_fields])
        c = Context({
            'form': self,
            'bound_fields': bound_fields,
            'bound_fields_dict':bound_fields_dict
        })
        t = loader.get_template(self.template)
        return t.render(c)
        
    def __unicode__(self):
        return self.output_via_template()
