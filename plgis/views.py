import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.gis.geos import Point
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, loader

from plgis.spatial.img import ajax_store_images, store_images

from .models import *
from .forms import *

# Create your views here.
MODELS = {
    'circuits': Circuit,
    'towers': Tower,
    'users': User

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


to_list = lambda iterable: [i for i in iterable]  # OMG... This should be posted to r/ProgrammerHumor


# TODO: Refactor this view as it shadows reference to list. I'm a freakin' genius
@login_required
def list(request):
    model_str = request.path.split('/')[1]
    model = MODELS[model_str]
    context = {
        'model_name': model_str,
        'headers': model.FIELDS.keys(),
        'objects': model.get_user_related_objects(request.user),
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
            task = request.POST.get('task', None)
            if task == "validate_circuit":
                data = json.loads(request.POST.get('data'))
                form = CircuitForm(data)
                if form.is_valid():
                    return JsonResponse({
                        "valid": True
                    })
                else:
                    return JsonResponse({
                        "valid": False,
                        "errors": form.errors
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
            for _, t in data['towers'].items():
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
    return HttpResponse(t.render(context, request))


@login_required
def user_profile(request, id):
    context = {
        'usr': User.objects.get(pk=id)
    }
    t = loader.get_template("plgis/profile.html")
    return HttpResponse(t.render(context, request))


@login_required
def img_upload(request):
    if request.method == 'POST':
        if request.is_ajax():
            if request.POST['command'] == 'pics_upload':
                msgs = ajax_store_images(request)
                return JsonResponse(msgs)
        else:
            # Form submit
            store_images(request)
            return redirect('inspection', circuit_id=request.POST['circuit'])
    else:
        t = loader.get_template("plgis/img_upload.html")
        context = {
            'circuits': Circuit.get_user_related_objects(request.user)
        }
        return HttpResponse(t.render(context, request))


@login_required
def img_list(request):
    t = loader.get_template("plgis/img_list.html")
    circuits = Circuit.get_user_related_objects(request.user)
    images = Image.objects.filter(circuit__in=[c.id for c in circuits])
    context = {
        'images': images
    }
    return HttpResponse(t.render(context, request))


@login_required
def inspection(request, circuit_id=None, section_id=None, image_id=None):
    if request.method == 'POST':
        # Here come the submitted markings
        marks = json.loads(request.POST['markings'])
        img = Image.objects.get(pk=image_id)
        img.inspected = True
        img.inspector = request.user
        img.save()
        for m in marks:
            fault = Fault(
                address=m['address'],
                component=m['component'],
                type=m['type'],
                severity=m['severity'],
                comment=m['comment'],
                author=request.user
            )
            fault.save()
            mm = Marking(
                image=img,
                fault=fault,
                marking=m['marking'],
            )
            mm.save()
        sights = json.loads(request.POST['sightings'])
        for s in sights:
            m = Marking(
                image=img,
                fault=Fault.objects.get(pk=s['fault']),
                marking=s['marking']
            )
            m.save()

    if circuit_id:
        circuit = Circuit.get_user_related_objects(request.user).get(pk=circuit_id)
        if section_id:
            images = Image.get_section_imagery(circuit_id, section_id)
            if image_id:
                image = Image.objects.get(pk=image_id)
                idx = [i.id for i in images].index(image_id)
                next_image = images[idx + 1 if not idx == len(images) - 1 else 0]
                prev_image = images[idx - 1 if not idx == 0 else len(images) - 1]
            else:
                return redirect('inspection', circuit_id=circuit_id, section_id=section_id, image_id=images[0].id)

            if 'SF-' in section_id:
                # If section is Span Field, the string has form SF-{t1.id padded}_{t2.id padded}
                t1, t2 = section_id.split('-')[1].split('_')
                # TODO: This might cause problems later. Some sort of lambda filter would be ideal
                t1 = circuit.get_towers().filter(identifier__endswith=t1)[0]
                t2 = circuit.get_towers().filter(identifier__endswith=t2)[0]
                macro = [t1, t2]
            else:
                macro = circuit.get_towers().get(identifier=section_id)

            marks = Marking.objects.filter(fault__address__circuit=str(circuit_id))
            faults = image.get_faults()
            circuit_faults = circuit.get_faults()
            nearby_faults = image.get_nearby_faults()
            recent_faults = Fault.get_recent_faults(circuit_id)
            components = circuit.get_components()
            types = circuit.get_types()
            context = {
                'images': images,
                'image': image,
                'next_image': next_image,
                'prev_image': prev_image,
                'section_type': 'tower' if isinstance(macro, Tower) else 'sf',
                'section': section_id,
                'macro': macro,
                'circuit': circuit,
                'marks': marks,
                'faults': faults,
                'nearby_faults': nearby_faults,
                'recent_faults': recent_faults,
                'circuit_faults': circuit_faults,
                'components': components,
                'types': types,
            }
            t = loader.get_template("plgis/inspection.html")
            return HttpResponse(t.render(context, request))
        else:
            towers = circuit.get_towers()
            span_fields = [f'SF-{towers[i].number}_{towers[i + 1].number}' for i in range(len(towers) - 1)]
            t = loader.get_template("plgis/inspection_select_section.html")
            context = {
                'circuit': circuit,
                'towers': towers,
                'span_fields': span_fields,
            }
            return HttpResponse(t.render(context, request))
    else:
        t = loader.get_template('plgis/inspection_select_circuit.html')
        context = {
            'circuits': Circuit.get_user_related_objects(request.user)
        }
        return HttpResponse(t.render(context, request))


@login_required
def marking(request, mark_id):
    pass


@login_required
def fault(request, fault_id):
    if request.method == 'POST':
        if request.is_ajax():
            data = request.POST
            response = {}
            if 'circuit' in data:
                circuit = Circuit.objects.get(pk=data['circuit'])
                c = circuit.component_tree()
                if 'section_type' in data:
                    st = data['section_type']
                    if 'section' in data:
                        s = data['section']
                        if 'traverse' in data:
                            t = data['traverse']
                            if 'side' in data:
                                sd = data['side']
                                if 'bundle' in data:
                                    b = data['bundle']
                                    if 'cable' in data:
                                        cb = data['cable']
                                    else:
                                        response['cable'] = [i + 1 for i in range(int(c[s].traverses[t]['bundles'][b]['cables']['count']))]
                                else:
                                    response['bundle'] = to_list(c[s].traverses[t]['bundles'].keys())
                            else:
                                response['side'] = ['L', 'M', 'R']
                        else:
                            response['traverse'] = to_list(c[s].traverses.keys())
                    else:
                        # cause I got enough memory...
                        response['section'] = [(c,c) for c in c.keys()] \
                            if st == 'tower' else \
                            [(t[0].identifier,f'SF-{t[0].number}_{t[1].number}') for t in circuit.get_span_fields()]
                else:
                    response['section_type'] = [('tower', 'Tower'), ('span_field', 'Span Field')]
            else:
                response['circuit'] = [(c.id, c.identifier) for c in Circuit.get_user_related_objects(request.user)]

            return JsonResponse(response)
    else:
        fault = Fault.objects.get(pk=fault_id)
        images = fault.get_images()
        marks = fault.get_marks()
        circuit = Circuit.objects.get(pk=fault.address['circuit'])
        components = circuit.get_components()
        types = circuit.get_types()
        context = {
            'fault': fault,
            'images': images,
            'marks': marks,
            'circuit': circuit,
            'components': components,
            'types': types,

        }
        t = loader.get_template('plgis/fault.html')
        return HttpResponse(t.render(context, request))
