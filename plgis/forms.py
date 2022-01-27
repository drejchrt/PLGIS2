from django import forms
from django.contrib.gis import forms as gforms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import *

class CircuitForm(ModelForm):
    class Meta:
        model = Circuit
        fields = ['identifier','voltage','substation_start','substation_end']
        labels = {
            'identifier': _('Circuit ID:'),
            'voltage': _('Voltage [kV]'),
            'substation_start': _('Starting Substation'),
            'substation_end': _('Ending Substation'),
        }

        ## https://docs.djangoproject.com/en/4.0/topics/forms/modelforms/

    def validate(self):
        pass

class TowerForm(ModelForm):
    position = gforms.PointField(widget=gforms.OSMWidget(attrs={
        'map_height':506,
        'map_width':760
    }))
    class Meta:
        model = Tower
        fields = '__all__'


class FaultEditForm(forms.Form):
    circuits = [(c.id,c.identifier) for c in Circuit.objects.all()]
    components = forms.ChoiceField()
    circuit = forms.ChoiceField()
    section = forms.ChoiceField()
    traverse = forms.ChoiceField()
    side = forms.ChoiceField()

    component = forms.ChoiceField()
    type = forms.ChoiceField()
    severity = forms.ChoiceField()
    comment = forms.Textarea()


class SpanFieldFaultEditForm(FaultEditForm):
    bundle = forms.ChoiceField()
    cables = forms.ChoiceField()