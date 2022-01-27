import os
import datetime
from plgis.misc.tools import touch

from django.contrib.gis.geos import Point
from django.conf import settings

from plgis.models import Circuit, Image

import exifread


def ajax_store_images(request):
    '''
    Store the images that were uploaded via ajax. This means, that here
    we should only work with the uploaded images, and not with the whole form.
    The images get stored in a temporary working directory and the DB Entries
    get created. If the files contain GPS Data in EXIF, these coordinates will
    be sotred as the image position in the DB and returned to the view
    in order to automatically display them in the coordinates input. These
    coordinates may be overridden upon form submit.
    :param request: request containtng the files
    :return: messages
    '''

    ## TODO: do file type check so that only images get uploaded
    def process_multiple_file_input(input, type):
        for p in request.FILES.getlist(input):
            # save images to a working directory
            fname = os.path.join(store_dir, p.name)
            touch(fname)
            with open(fname, 'wb+') as f:
                for chunk in p.chunks():
                    f.write(chunk)
            # Create a DB entry for each image
            i = Image(path=fname)
            msgs['info'].append(f'{i.get_fname()} stored!')
            # Try to get the coordinates from EXIF
            try:
                lat, lon, alt = get_gps_coords_from_exif(fname)
                msgs['exif_coords'][type].append(f'{i.get_fname()},{lat},{lon},{alt}\n')
                i.position = Point(lon, lat, alt, srid=4326)

            except KeyError:
                msgs['warn'].append(f'Couldn\'t read coords from {i.get_fname()}')
            i.properties = {'type': type}
            i.author=request.user
            i.save()

    msgs = {
        'error': [],
        'warn': [],
        'info': [],
        'exif_coords': {
            'tower': [],
            'span_field': [],
        },
    }

    store_dir = os.path.join(
        settings.MEDIA_ROOT,
        'imagery',
        'circuits',
        'wd'
    )

    process_multiple_file_input('mast-pics', 'tower')
    process_multiple_file_input('sf-pics', 'span_field')

    return msgs


def store_images(request):
    # extract data from the form
    c = Circuit.get_user_related_objects(request.user).get(pk=request.POST['circuit'])
    sep = request.POST['coords_separator']
    srid = request.POST['coords_srid']
    # convert the coord lists into dictionaries, for quick coord lookup by img name
    cl = {}
    for row in (request.POST['mast_coords'] + request.POST['sf_coords']).split('\n'):
        row_splt = row.split(sep)
        if len(row_splt) == 3:
            name, x, y = row_splt
            z = -99999
        elif len(row_splt) == 4:
            name, x, y, z = row.split(sep)
        # TODO: else raise some exception (ValueError??)
        cl[name] = [x, y, z]
    # get images that were stored in the working directory by the ajax call
    imgs = Image.get_working_directory_imagery()
    for img in imgs:
        # Fill in the missing fields
        img.circuit = c
        type = img.properties['type']
        coords = cl[img.get_fname()]
        img.position = Point(float(coords[0]), float(coords[1]), float(coords[2]), srid=srid)
        if type == 'tower':
            tower = c.get_nearest_tower(img.position)
            img.properties['section'] = tower.identifier
        else:
            sf = c.get_nearest_span_field(img.position)
            img.properties['section'] = sf['name']

        img.move(img.get_path_from_properties())
        img.save()


def get_gps_coords_from_exif(path):
    """
    Extracts GPS coordinates from an Image
    :param path:
    :return:
    """
    sex2deg = lambda deg, min, sec: deg + min / 60 + sec / 3600

    with open(path, 'rb') as f:
        pf = exifread.process_file(f)
        lat = pf['GPS GPSLatitude']
        lon = pf['GPS GPSLongitude']
        lat = sex2deg(int(lat.values[0].num), int(lat.values[1].num), lat.values[2].num / lat.values[2].den)
        lon = sex2deg(int(lon.values[0].num), int(lon.values[1].num), lon.values[2].num / lon.values[2].den)
        try:
            alt = float(pf['GPS GPSAltitude'].values[0].num / pf['GPS GPSAltitude'].values[0].den)
        except KeyError:
            # TODO: stderr/stdwarn
            print('Altitude could not be extracted. Setting the value to -99999 ')
            alt = -99999

    return lat, lon, alt

