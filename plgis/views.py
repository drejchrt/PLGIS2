from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.gis.geos import Point
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, loader
from django.urls import reverse
from django.views.generic import ListView

import json

from .models import *
from .forms import *

# Create your views here.
MODELS = {
    'circuits': Circuit,
    'towers': Tower,

}
FORMS = {
    'circuits': CircuitForm,
    'towers': TowerForm,
}


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')

    t = loader.get_template("plgis/dashboard.html")
    return HttpResponse(t.render({}, request))


def request_new_account(request):
    pass


@login_required
def lookup(request, query):
    pass


@login_required
def list(request):
    model_str = request.path.split('/')[1]
    model = MODELS[model_str]
    context = {
        'model_name': model_str,
        'headers': model.FIELDS.keys(),
        'objects': model.objects.all(),
        'fields': model.FIELDS.values(),
    }
    t = loader.get_template("plgis/list.html")
    return HttpResponse(t.render(context, request))


@login_required
def detail(request, id):
    model_str = request.path.split('/')[1]
    model = MODELS[model_str]
    context = {
        'model_name': model_str,
        'headers': model.FIELDS.keys(),
        'object': model.objects.get(pk=id),
        'fields': model.FIELDS.values(),
    }
    t = loader.get_template("plgis/detail.html")
    if model_str == 'circuits':
        context['towers'] = Tower.objects.filter(circuit_id=id)
        context['t_headers'] = Tower.FIELDS.keys()
        context['t_fields'] = Tower.FIELDS.values()
    return HttpResponse(t.render(context, request))


@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def edit(request, id):
    model_str = request.path.split('/')[1]
    model = MODELS[model_str]
    form_class = FORMS[model_str]
    form = form_class(request.POST or None, instance=model.objects.get(pk=id))
    context = {
        'model_name': model_str,
        'form': form,
        'headers': model.FIELDS.keys(),
        'object': model.objects.get(pk=id),
        'fields': model.FIELDS.values(),
    }

    if request.method == "POST":

        if form.is_valid():
            form.save()
            messages.success(request, 'Changes successfully saved!')
            redirect(model_str[:-1], id=id)
        else:
            messages.error(request, "Error - Input data invalid")
            context['form'] = form

    t = loader.get_template("plgis/edit.html")
    return HttpResponse(t.render(context, request))


@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def delete(request, id):
    model_str = request.path.split('/')[1]
    model = MODELS[model_str]
    model.objects.get(pk=id).delete()
    messages.success(request, f"{model_str[:-1].capitalize()} successfully deleted")
    return redirect(model_str)


@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def new(request):
    model_str = request.path.split('/')[1]
    model = MODELS[model_str]
    form_class = FORMS[model_str]

    if request.method == 'POST':
        if request.is_ajax():  # Handle live validation requests
            # TODO: Finish this part later
            return JsonResponse(dict(request.POST))
        else:  # Handle form submission
            form = form_class(request.POST)
            if form.is_valid():
                form.save()
                if 'save' in request.POST:  # submitted with the save button
                    messages.success(request, model_str[:-1] + ' created successfully!')
                    return HttpResponseRedirect(reverse(model_str))
                else:  # submitted with the save and next button
                    return redirect(model_str[:-1] + '_new')
            else:
                messages.error(request, "Error - Input data invalid")

                context = {
                    'model_name': model_str,
                    'headers': model.FIELDS.keys,
                    'form': form
                }
                t = loader.get_template("plgis/new.html")
                return HttpResponse(t.render(context, request))

    else:  # load the page with a form
        context = {
            'model_name': model_str,
            'headers': model.FIELDS.keys,
            'form': form_class()
        }
        t = loader.get_template("plgis/new.html")
        return HttpResponse(t.render(context, request))

@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def constructor(request):
    if request.POST:
        if request.is_ajax():
            task = request.POST.get('task',None)
            if task == "validate_circuit":
                data = json.loads(request.POST.get('data'))
                form = CircuitForm(data)
                if form.is_valid():
                    return JsonResponse({
                        "valid":True
                    })
                else:
                    return JsonResponse({
                        "valid":False,
                        "errors":form.errors
                    })
        else:
            data = json.loads(request.POST['data'])
            circuit = Circuit(identifier=data['identifier'],
                              voltage=data['voltage'],
                              substation_start=data['substation_start'],
                              substation_end=data['substation_end']
                              )
            circuit.save()
            print(data)
            for _,t in data['towers'].items():
                tower = Tower(identifier=t['identifier'],
                              circuit=circuit,
                              type=t['type'],
                              position=Point(float(t['position']['x']),
                                             float(t['position']['y']),
                                             srid=t['position']['srid']
                                             ),
                              components=t['components'],
                              traverses=t['traverses'],
                              )
                tower.save()
            print(data)

    context = {
        'circuit_form': CircuitForm()
    }
    t = loader.get_template("plgis/constructor.html")
    return HttpResponse(t.render(context,request))
