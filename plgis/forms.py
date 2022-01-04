from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import *


class CircuitForm(ModelForm):
    class Meta:
        model = Circuit
        fields = '__all__'
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
    class Meta:
        model = Tower
        fields = '__all__'


class SpanFieldForm(ModelForm):
    class Meta:
        model = SpanField
        fields = '__all__'

class ComponentForm(ModelForm):
    class Meta:
        model = Component
        fields = '__all__'