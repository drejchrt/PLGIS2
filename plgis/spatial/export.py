import datetime
import os
import shutil

from django.conf import settings

import pandas as pd
import geopandas as gpd
from pyproj import Transformer

from plgis.misc.tools import touch
from plgis.models import Tower, Image, Marking

FORMATS = {
    'gpkg': {'extension': 'gpkg', 'driver': 'GPKG'},
    'shp': {'extension': 'shp', 'driver': 'ESRI Shapefile'},
    'geojson': {'extension': 'geojson', 'driver': 'GeoJSON'},
    'dxf': {'extension': 'dxf', 'driver': 'DXF'},
    'gml': {'extension': 'gml', 'driver': 'GML'},
    'csv': {'extension': 'csv', 'driver': 'CSV'},
}


def export(request):
    data = request.POST
    t_ids = [t.split('-')[1] for t in data.keys() if 'towers' in t]
    towers = Tower.objects.filter(id__in=t_ids)
    sfs = [sf for sf in data.keys() if 'SF-' in sf]
    t_srid = int(data['srid'])
    ext = FORMATS[data['geo_format']]['extension']
    driver = FORMATS[data['geo_format']]['driver']

    ts = int(datetime.datetime.now().timestamp())
    edir = os.path.join(settings.MEDIA_ROOT, 'export', 'temp_' + str(ts))

    if 'elem_faults' in data:
        t_faults = Marking.objects.filter(fault__address__section__in=[t.identifier for t in towers])
        sf_faults = Marking.objects.filter(fault__address__section__in=sfs)

        df = {
            'img_id': [],
            'img_name': [],
            'img_path': [],
            'fault_id': [],
            'marking': [],
            'component': [],
            'type': [],
            'severity': [],
            'comment': []
        }
        wkts = []
        for m in list(t_faults) + list(sf_faults):
            df['img_id'].append(m.image.id)
            df['img_name'].append(m.image.get_fname())
            df['img_path'].append(os.path.join(edir, 'images', m.image.properties['section'], m.image.get_fname()))
            df['fault_id'].append(m.fault.id)
            df['marking'].append(m.marking)
            df['component'].append(m.fault.component)
            df['type'].append(m.fault.type)
            df['severity'].append(m.fault.severity)
            df['comment'].append(m.fault.comment)
            c_srid = m.image.position.srid
            if not c_srid == t_srid:
                trafo = Transformer.from_crs(c_srid, t_srid)
                x, y = trafo.transform(m.image.position.x, m.image.position.y)
                wkt = f'POINT({x} {y})'
                wkts.append(wkt)
            else:
                wkts.append(m.image.position.wkt)

        df = pd.DataFrame(df)
        gs = gpd.GeoSeries.from_wkt(wkts)
        gdf = gpd.GeoDataFrame(df, geometry=gs, crs=f"EPSG:{t_srid}")

        gdf_to_file(gdf, ext, driver, edir, 'marks')

    if 'elem_images' in data:
        imgs_t = Image.objects.filter(properties__section__in=[t.identifier for t in towers])
        imgs_sf = Image.objects.filter(properties__section__in=sfs)

        for img in list(imgs_t) + list(imgs_sf):
            img.copy_file(os.path.join(edir, 'images', img.properties['section'], img.get_fname()))

    if 'elem_img_pos' in data:
        imgs_t = Image.objects.filter(properties__section__in=[t.identifier for t in towers])
        imgs_sf = Image.objects.filter(properties__section__in=sfs)

        df = {
            'id': [],
            'name': [],
            'path': [],
            'inspected': [],
            'inspector': [],
            'author': [],
            'date_uploaded': [],
            'date_taken': [],
            'dimensions': [],
        }
        wkts = []

        for img in list(imgs_t) + list(imgs_sf):
            df['id'].append(img.id)
            df['name'].append(img.get_fname())
            df['path'].append(os.path.join(edir, 'images', img.properties['section'], img.get_fname()))
            df['inspected'].append(img.inspected)
            df['inspector'].append(img.inspector.username)
            df['author'].append(img.author.username)
            df['date_uploaded'].append(img.date_uploaded.strftime('%Y%m%d_%H%M%S'))
            df['date_taken'].append(img.get_date_taken().strftime('%Y%m%d_%H%M%S'))
            df['dimensions'].append(f'{img.get_dimensions()[0]} x {img.get_dimensions()[1]}')

            c_srid = img.position.srid
            if not c_srid == t_srid:
                trafo = Transformer.from_crs(c_srid, t_srid)
                x, y = trafo.transform(img.position.x, img.position.y)
                wkt = f'POINT({x} {y})'
                wkts.append(wkt)
            else:
                wkts.append(img.position.wkt)

        df = pd.DataFrame(df)
        gs = gpd.GeoSeries.from_wkt(wkts)
        gdf = gpd.GeoDataFrame(df, geometry=gs, crs=f"EPSG:{t_srid}")

        gdf_to_file(gdf, ext, driver, edir, 'cam_pos')

    if 'elem_circuit' in data:
        df = {
            'id': [],
            'identifier': [],
            'circuit': [],
            'type': [],
            'components': [],
            'traverses': [],
            'bundles': [],
            'cables': [],
        }
        wkts = []
        for t in towers:
            df['id'].append(t.id)
            df['identifier'].append(t.identifier)
            df['circuit'].append(t.circuit.identifier)
            df['type'].append(t.type)
            df['components'].append(",".join([str(c) for c in t.components]))
            df['traverses'].append(len(t.get_traverses()))
            df['bundles'].append(len(t.get_bundles()))
            df['cables'].append(sum([int(c['count']) for c in t.get_cables()]))
            c_srid = t.position.srid
            if not c_srid == t_srid:
                trafo = Transformer.from_crs(c_srid, t_srid)
                x, y = trafo.transform(t.position.x, t.position.y)
                wkt = f'POINT({x} {y})'
                wkts.append(wkt)
            else:
                wkts.append(t.position.wkt)

        df = pd.DataFrame(df)
        gs = gpd.GeoSeries.from_wkt(wkts)
        gdf = gpd.GeoDataFrame(df, geometry=gs, crs=f"EPSG:{t_srid}")

        gdf_to_file(gdf, ext, driver, edir, 'circuit')


    ofile = os.path.join(settings.MEDIA_ROOT, 'export', f'export_plgis_{ts}')
    shutil.make_archive(ofile, 'zip', edir)
    return ofile + '.zip'


def gdf_to_file(gdf, ext, driver, edir, fname):
    if ext == 'gpkg':
        fpath = os.path.join(edir, f'{fname}.{ext}')
        # touch(fpath)
        gdf.to_file(fpath, driver=driver, layer=fname, mode='w')
    elif ext == 'shp':
        dir = os.path.join(edir, fname)
        os.makedirs(dir)
        gdf.to_file(dir, mode='w')
    else:
        fpath = os.path.join(edir, f'{fname}.{ext}')
        touch(fpath)
        gdf.to_file(fpath, driver=driver)
