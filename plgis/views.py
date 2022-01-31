import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.gis.geos import Point
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, loader

from plgis.spatial.img import ajax_store_images, store_images
from plgis.spatial.export import export as file_export

from .models import *
from .forms import *

# These constants are used by the list, detail, edit, new views.
# They provide the references to the models and forms, using strings
# extracted from url
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
    """
    This view serves the home page or the login page, based on whether
    the user is logged in or not
    """
    if not request.user.is_authenticated:
        return redirect('login')

    # TODO: Implement
    t = loader.get_template("plgis/dashboard.html")
    return HttpResponse(t.render({}, request))


def e404(request,exception):
    t = loader.get_template('plgis/e404.html')
    return HttpResponse(t.render({}, request))


# This might be implemented later. The sysadmin should know who is using
# the app. User accounts can be set in the admin app.
def request_new_account(request):
    pass


# This view will handle queries form the search bar placed on the topbar
# TODO: Implement
@login_required
def lookup(request, query):
    pass


# This is such a boner...
to_list = lambda iterable: [i for i in iterable]  # OMG... This should be posted to r/ProgrammerHumor


# TODO: Refactor this view as it shadows reference to list. I'm a freakin' genius
@login_required
def list(request):
    """
    This view serves to list out macro components, like towers and circuits.
    :param request: http request
    :return: http response
    """
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
    """
    This view serves to view attributes of the macro components
    :param request: http request
    :param id: id of the component
    :return: http response
    """
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
    """
    This view handles editing view and the edit forms of the respective macro components
    :param request: http request
    :param id: id of the component
    :return: http response
    """
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

    # Form Submit:
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, 'Changes successfully saved!')
            redirect(model_str[:-1], id=id)
        else:
            messages.error(request, "Error - Input data invalid")
            context['form'] = form

    # Display Form
    t = loader.get_template("plgis/edit.html")
    return HttpResponse(t.render(context, request))


@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def delete(request, id):
    """
    This view deletes a macro component.
    :param request: http request
    :param id: id of the component
    :return: http response
    """
    model_str = request.path.split('/')[1]
    model = MODELS[model_str]
    model.objects.get(pk=id).delete()
    messages.success(request, f"{model_str[:-1].capitalize()} successfully deleted")
    return redirect(model_str)


@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def new(request):
    """
    This view creates a new macro. Type is decided by the url.
    :param request: http request
    :return: http response"""

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


#######################################################################################################################

@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def constructor(request):
    """
    This view creates a circuit and towers in one single form, instead of creating
    every tower individually.
    :param request: http request
    :return: http/json response
    """
    if request.POST:
        if request.is_ajax():
            # AJAX calls made for input validation and such.
            task = request.POST.get('task', None)  # get value or None (= no Key Error)
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
            # Submit data from forms
            data = json.loads(request.POST['data'])
            circuit = Circuit(identifier=data['identifier'],
                              voltage=data['voltage'],
                              substation_start=data['substation_start'],
                              substation_end=data['substation_end']
                              )
            circuit.save()
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

    # disaply form
    context = {
        'circuit_form': CircuitForm()
    }
    t = loader.get_template("plgis/constructor.html")
    return HttpResponse(t.render(context, request))


@login_required
def user_profile(request, id):
    """
    This view display an user profile
    :param request: http request
    :param id: user id
    :return: http response
    """
    context = {
        'usr': User.objects.get(pk=id)
    }
    t = loader.get_template("plgis/profile.html")
    return HttpResponse(t.render(context, request))


@login_required
def img_upload(request):
    """
    This view uploads set of images. The image files get immediately uploaded
    via AJAX and stored in a temporary location. This view tries to
    read coordinates of the photographs stroed in exif. If valid coordinates
    are available, they get returend to the page and are placed into the
    coordinates textarea. If the user is satisfied, no action is required. In
    case the user has another external set of coordinates for each picture,
    e.g. (PPK) he can provide those coordinates. After submission the files
    will be moved to their designated path determined by the coordinates.
    :param request: http request
    :return: http/json/xhr response
    """
    if request.method == 'POST':
        if request.is_ajax():
            if request.POST['command'] == 'pics_upload': # file upload
                msgs = ajax_store_images(request)
                return JsonResponse(msgs)
        else:
            # Form submit
            store_images(request)
            return redirect('inspection', circuit_id=request.POST['circuit'])
    else:
        # render form
        t = loader.get_template("plgis/img_upload.html")
        context = {
            'circuits': Circuit.get_user_related_objects(request.user)
        }
        return HttpResponse(t.render(context, request))

########################################################################################################################
@login_required
def image(request, circuit_id=None, section_id=None, image_id=None):
    """
    This view handles listing and displaying of images. If the view does not
    receive specific image id, it shows a filtered set of image, based on
    the other view parameters (circuit and section)
    :param request:
    :param circuit_id:
    :param section_id:
    :param image_id:
    :return:
    """
    if circuit_id:
        circuit = Circuit.objects.get(pk=circuit_id)
        if section_id:
            images = Image.objects.filter(circuit=circuit).filter(properties__section=section_id)
            if image_id:
                # display specific image
                img = Image.objects.get(pk=image_id)
                marks = Marking.objects.filter(image=img)
                faults = [m.fault for m in marks]
                t = loader.get_template("plgis/image.html")
                context = {
                    'circuit': circuit,
                    'image': img,
                    'marks': marks,
                    'faults': faults

                }
                return HttpResponse(t.render(context, request))
            else:
                # list images in the section
                t = loader.get_template('plgis/list_images.html')
                context = {
                    'images': images
                }
                return HttpResponse(t.render(context, request))

        else:
            # list images in the circuit
            towers = circuit.get_towers()
            span_fields = [f'SF-{towers[i].number}_{towers[i + 1].number}' for i in range(len(towers) - 1)]
            t = loader.get_template("plgis/select_section.html")
            context = {
                'circuit': circuit,
                'towers': towers,
                'span_fields': span_fields,
                'view': 'image',
                'images': Image.objects.filter(circuit=circuit)
            }
            return HttpResponse(t.render(context, request))
    else:
        # select cricuit
        t = loader.get_template('plgis/select_circuit.html')
        circuits = Circuit.get_user_related_objects(request.user)
        images = Image.objects.filter(circuit__in=circuits)
        context = {
            'circuits': Circuit.get_user_related_objects(request.user),
            'view': 'image',
            'images': images
        }
        return HttpResponse(t.render(context, request))


@login_required
def inspection(request, circuit_id=None, section_id=None, image_id=None):
    """
    This view takes care of the inspection. In this view user can annotate the
    uploaded pictures by creating rectangular markings. After the marking, user
    can either associate the marking with an already existing fault, or
    register a new one. In order to make it easier for the user to select
    already created fault, the view provides a geographically nearest faults
    as well as faults that got recently edited. If specific image_id is not
    provided, let's the user select from a containing entity (circuit, section)
    :param request:
    :param circuit_id:
    :param section_id:
    :param image_id:
    :return:
    """
    if request.method == 'POST':
        # Handle the submitted markings
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
                # inspect specific image
                image = Image.objects.get(pk=image_id)
                idx = [i.id for i in images].index(image_id)
                next_image = images[idx + 1 if not idx == len(images) - 1 else 0]
                prev_image = images[idx - 1 if not idx == 0 else len(images) - 1]
            else:
                # inspect the first image of the section
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
            # select section
            towers = circuit.get_towers()
            span_fields = [f'SF-{towers[i].number}_{towers[i + 1].number}' for i in range(len(towers) - 1)]
            t = loader.get_template("plgis/select_section.html")
            context = {
                'circuit': circuit,
                'towers': towers,
                'span_fields': span_fields,
                'view': 'inspection',
            }
            return HttpResponse(t.render(context, request))

    else:
        # select circuit
        t = loader.get_template('plgis/select_circuit.html')
        context = {
            'circuits': Circuit.get_user_related_objects(request.user),
            'view': 'inspection',
        }
        return HttpResponse(t.render(context, request))

@login_required
def fault(request, circuit_id=None, section_id=None, fault_id=None):
    """
    This view handles listing and displaying of faults. If the view does not
    receive specific image id, it shows a filtered set of image, based on
    the other view parameters (circuit and section)
    """
    if circuit_id:
        circuit = Circuit.get_user_related_objects(request.user).get(pk=circuit_id)
        if section_id:
            faults = circuit.get_faults()
            if fault_id:
                if request.method == 'POST':
                    if request.is_ajax():
                        # TODO: MAke it work properly
                        # load address values into the edit form
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
                                                    response['cable'] = [i + 1 for i in range(
                                                        int(c[s].traverses[t]['bundles'][b]['cables']['count']))]
                                            else:
                                                response['bundle'] = to_list(c[s].traverses[t]['bundles'].keys())
                                        else:
                                            response['side'] = ['L', 'M', 'R']
                                    else:
                                        response['traverse'] = to_list(c[s].traverses.keys())
                                else:
                                    # cause I got enough memory...
                                    response['section'] = [(c, c) for c in c.keys()] \
                                        if st == 'tower' else \
                                        [(t[0].identifier, f'SF-{t[0].number}_{t[1].number}') for t in
                                         circuit.get_span_fields()]
                            else:
                                response['section_type'] = [('tower', 'Tower'), ('span_field', 'Span Field')]
                        else:
                            response['circuit'] = [(c.id, c.identifier) for c in
                                                   Circuit.get_user_related_objects(request.user)]

                        return JsonResponse(response)
                    else:
                        # Handle edit-form submit
                        pass

                else:
                    # Display fault page
                    if 'SF-' in section_id:
                        # If section is Span Field, the string has form SF-{t1.id padded}_{t2.id padded}
                        t1, t2 = section_id.split('-')[1].split('_')
                        # TODO: This might cause problems later. Some sort of lambda filter would be ideal
                        t1 = circuit.get_towers().filter(identifier__endswith=t1)[0]
                        t2 = circuit.get_towers().filter(identifier__endswith=t2)[0]
                        macro = [t1, t2]
                    else:
                        macro = circuit.get_towers().get(identifier=section_id)

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
                        'section': section_id,

                    }
                    t = loader.get_template('plgis/fault.html')
                    return HttpResponse(t.render(context, request))
            else:
                # Select from section
                t = loader.get_template('plgis/list_faults.html')
                context = {
                    'faults': Fault.objects.filter(address__circuit=str(circuit_id)).filter(address__section=section_id)
                }
                return HttpResponse(t.render(context, request))
        else:
            # Select from circuit
            towers = circuit.get_towers()
            span_fields = [f'SF-{towers[i].number}_{towers[i + 1].number}' for i in range(len(towers) - 1)]
            t = loader.get_template("plgis/select_section.html")
            context = {
                'circuit': circuit,
                'towers': towers,
                'span_fields': span_fields,
                'view': 'fault',
                'faults': Fault.objects.filter(address__circuit=str(circuit_id))
            }
            return HttpResponse(t.render(context, request))
    else:
        # Select circuit
        t = loader.get_template('plgis/select_circuit.html')
        circuits = [str(c.id) for c in Circuit.get_user_related_objects(request.user)]
        context = {
            'circuits': Circuit.get_user_related_objects(request.user),
            'view': 'fault',
            'faults': Fault.objects.filter(address__circuit__in=circuits)
        }
        return HttpResponse(t.render(context, request))


@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def export(request):
    """
    This view handles the export. The user can select circuit, sections-only,
    geometry format, epsg code, and what data (geometry, attributes, images).
    The selected data get copied into one zip archive and the archive is
    served as an request attachment to be downloaded.
    :param request:
    :return:
    """
    if request.method == 'POST':
        if request.is_ajax():
            # Based on a selected circuit provide available sections
            data = json.loads(request.body)
            cid = data['circuit']
            circuit = Circuit.objects.get(pk=cid)
            response = {
                'towers': [{'id': t.id, 'name': t.identifier} for t in circuit.get_towers()],
                'spanfields': circuit.get_span_fields(return_towers=False),
            }
            return JsonResponse(response)
        else:
            # Prepare the data for export and serve them
            fpath = file_export(request)
            with open(fpath, 'rb') as f:
                response = HttpResponse(f, content_type='application/force-download')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(fpath)}"'
                return response

    else:
        # Display the form
        t = loader.get_template('plgis/export.html')
        context = {
            'circuits': Circuit.get_user_related_objects(request.user)
        }
        return HttpResponse(t.render(context, request))


@login_required
@user_passes_test(lambda u: u.groups.filter(name='managers').exists())
def stats(request):
    # TODO: Implement
    pass
