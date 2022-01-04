from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, loader
from django.urls import reverse
from django.views.generic import ListView

from .models import *
from .forms import *

# Create your views here.
MODELS = {
    'circuits': Circuit,
    'towers': Tower,
    'spanfields': SpanField,
    'components': Component,
}
FORMS = {
    'circuits': CircuitForm,
    'towers': TowerForm,
    'spanfields': SpanFieldForm,
    'components': ComponentForm,
}


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')

    t = loader.get_template("plgis/dashboard.html")
    return HttpResponse(t.render({}, request))


@login_required
def constructor(request):
    pass


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
        'headers': model.FIELDS.keys,
        'object': model.objects.get(pk=id),
        'fields': model.FIELDS.values(),
    }
    t = loader.get_template("plgis/detail.html")
    return HttpResponse(t.render(context, request))


@login_required
def edit(request, model):
    pass


@login_required
def delete(request, model):
    pass


@login_required
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
                print(request.POST)
                if 'save' in request.POST: # submitted with the save button
                    messages.success(request, model_str[:-1] + ' created successfully!')
                    return HttpResponseRedirect(reverse(model_str))
                else: # submitted with the save and next button
                    return redirect(model_str[:-1] + '_new')
            else:
                m = 'Error:\n'
                m += '\n'.join([f'\t {err}: {det}' for err, det in form.error_messages.items()])
                messages.error(request,m)

                context = {
                    'model_name': model_str,
                    'headers': model.FIELDS.keys,
                    'form': form_class()
                }
                t = loader.get_template("plgis/new.html")
                return HttpResponse(t.render(context, request))

    else: # load the page with a form
        context = {
            'model_name': model_str,
            'headers': model.FIELDS.keys,
            'form': form_class()
        }
        t = loader.get_template("plgis/new.html")
        return HttpResponse(t.render(context, request))
