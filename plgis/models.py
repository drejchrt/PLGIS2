from datetime import datetime
import os
from operator import itemgetter

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, MultiPoint
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse

from plgis.misc.tools import fkin_move_file, fkin_copy_file, get_date_taken_from_exif

import PIL


########################################## Macro Components ############################################################

class Circuit(models.Model):
    identifier = models.CharField(max_length=255, unique=True)
    voltage = models.IntegerField()
    substation_start = models.CharField(max_length=255, blank=True)
    substation_end = models.CharField(max_length=255, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    FIELDS = {
        'ID': identifier,
        'Voltage': voltage,
        'Start': substation_start,
        'End': substation_end,
        'Date Added': date_added,
    }

    def get_absolute_url(self):
        return reverse('circuit', kwargs={'id': self.pk})

    ## This method feels wierd...
    @classmethod
    def get_user_related_objects(cls, user):
        return user.profile.circuits.all()

    def get_towers(self):
        return Tower.objects.filter(circuit=self)

    def get_span_fields(self,return_towers=True):
        towers = self.get_towers()
        if return_towers:
            return [[towers[i], towers[i + 1]]  for i in range(len(towers) - 1)]
        else:
            return [f'SF-{towers[i].number}_{towers[i + 1].number}' for i in range(len(towers) - 1)]

    def component_tree(self):
        return {t.identifier:t for t in self.get_towers()}

    def get_nearest_tower(self, point, max_valid_dist=0):
        '''
        Returns a tower of the circuit, that is the nearest to specified point
        One can also specify maximal valid distance, e.g. if the the nearest tower
        is further than 50 meters, it is not likely, that the point has a relation to
        the point. However this feature is off per default (max_valid_dist=0)
        :param point: <GEOSGeometry.Point> Point for which the nearest tower is searched
        :param max_valid_dist: <float> Maximal allowed distance from any tower
        :return: <plgis.models.Tower/None> Instance of Tower model closest to the point or None
        '''

        # Since there is usually less than 1000 Towers in a Circiut, so it does not make sense
        # to build a k-d tree or something in order to find the neighbours quicker. Let's just
        # find the minimum distance by comparing distances to all towers.

        towers = self.get_towers()
        tmin = None
        dmin = float('inf')
        for t in towers:
            d = t.position.distance(point)
            if d < dmin:
                tmin = t
                dmin = d
        return tmin

    def get_nearest_span_field(self, point, max_valid_dist=0):
        """
        Returns nearses spanfiled to the specicfied point.
        One can also specify maximal valid distance, e.g. if the the nearest tower
        is further than 50 meters, it is not likely, that the point has a relation to
        the point. However this feature is off per default (max_valid_dist=0)
        :param point: <GEOSGeometry.Point> Point for which the nearest tower is searched
        :param max_valid_dist: <float> Maximal allowed distance from any tower
        :return: <dict> Dictionary representing the nearest spanfield.
                 keys: name (str) and geometry (GEOSGeometry.LineString)
        """
        # create spanfield geometries
        towers = self.get_towers()
        sfs = [{
            'name': f'SF-{towers[i].number}_{towers[i + 1].number}',
            'geom': LineString(towers[i].position, towers[i + 1].position)
        } for i in range(len(towers) - 1)]
        dmin = float('inf')
        sfmin = None
        for sf in sfs:
            d = point.distance(sf['geom'])
            if d < dmin:
                dmin = d
                sfmin = sf
        return sfmin

    def get_images(self):
        return Image.objects.filter(circuit=self)

    def get_faults(self):
        return Fault.objects.filter(address__circuit=str(self.id))

    def get_marks(self):
        return Marking.objects.filter(image__circuit=self)

    def get_components(self):
        return set([f.component for f in Fault.objects.filter(address__circuit=str(self.id))])

    def get_types(self):
        return set([f.type for f in Fault.objects.filter(address__circuit=str(self.id))])


    def __repr__(self):
        return self.identifier

    def __str__(self):
        return self.__repr__()


class Tower(models.Model):
    identifier = models.CharField(max_length=255)
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE)
    type = models.CharField(max_length=255)  # TODO: Choices
    components = ArrayField(models.CharField(max_length=255), default=list)
    position = models.PointField()
    traverses = JSONField(default=dict) # Check example structres at bottom of this file:

    FIELDS = {
        'ID': identifier,
        'Circuit': circuit,
        'Type': type,
        'Components': components,
        'Position': position
    }

    def get_absolute_url(self):
        return reverse('tower', kwargs={'id': self.pk})

    # TODO: Make sure this works
    @classmethod
    def get_user_related_objects(cls, user):
        circuits = user.profile.circuits.all()
        return cls.objects.filter(circuit__in=circuits)

    @property
    def number(self):
        return "".join([c for c in self.identifier if c.isdigit()])

    def get_traverses(self):
        return [t for _,t in self.traverses.items()]

    def get_bundles(self):
        bundles = []
        tb = [(t['number'],t['bundles']) for t in self.get_traverses()]
        for tn,t in tb:
            b_names = t.keys()
            for bn in b_names:
                t[bn]['traverse'] = tn
                bundles.append(t[bn])

        return bundles

    def get_cables(self):
        return [b['cables'] for b in self.get_bundles()]


# django.contrib.auth.model.User extenstion
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    tel = models.CharField(max_length=50)
    picture = models.ImageField(upload_to='profile_pics')

    circuits = models.ManyToManyField(Circuit)


# save Profile instance wiht user
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

############################################# Inspection Elements ######################################################

class Image(models.Model):
    path = models.FilePathField(path=settings.MEDIA_ROOT, max_length=255)
    circuit = models.ForeignKey(Circuit, on_delete=models.SET_NULL, null=True)
    properties = models.JSONField(default=dict) # Check the JSON examples on the bottom of this files
    position = models.PointField(null=True, dim=3)
    inspected = models.BooleanField(default=False)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspecotr')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='author')
    date_uploaded = models.DateTimeField(auto_now_add=True)

    # TODO: Store some of these values into table? (to spare some file system accesses)
    def get_size(self):
        # Size in MB
        return os.stat(self.path).st_size / 1000000.0

    # TODO Store this as table field,
    def get_dimensions(self):
        with PIL.Image.open(self.path) as img:
            return img.size


    def get_date_taken(self):
        try:
            return get_date_taken_from_exif(self.path)
        except (KeyError, TypeError):
            return datetime.fromtimestamp(0)


    def get_fname(self):
        return os.path.basename(self.path)

    def get_path_from_properties(self): # The path on the FS is given by the image properties => Automatic sorting
        if self.properties['type'] == 'tower':
            tdir = 'towers'
        else:
            tdir = 'span_fields'
        return os.path.join(
            settings.MEDIA_ROOT,
            'imagery',
            'circuits',
            f'{self.circuit.id}_{self.circuit.identifier}',
            tdir,
            self.properties['section'],
            self.get_fname()
        )

    def get_media_path(self): # Get the path based on the MEDIA_ROOT variable
        nodes = self.path.split(os.sep)
        media = nodes.index('media')
        return os.sep.join(nodes[media:])

    def get_inspection_path(self): # Link to inspection of this image
        kw = {
            'circuit_id': self.circuit.id,
            'section_id': self.properties['section'],
            'image_id': self.id
        }
        return reverse('inspection', kwargs=kw)

    @classmethod
    def get_working_directory_imagery(cls): # Get the images stored in the temporary working directory
        return Image.objects.filter(path__contains='wd')

    @classmethod
    def get_section_imagery(cls, circuit, section):
        cfilt = cls.objects.filter(circuit=circuit)
        return cfilt.filter(properties__section=section)

    def move(self, dest): # move the file and update the DB entry (the instance must be saved afterwards)
        fkin_move_file(self.path, dest)
        self.path = dest

    def copy_file(self, dest): # copy the file. (No DB entry manipulation)
        fkin_copy_file(self.path, dest)


    def get_faults(self):
        '''
        Gets Faults that are marked on this image
        :return:
        '''
        return [m.fault for m in Marking.objects.filter(image__id=self.id)]

    def get_nearby_faults(self, k=10):
        '''
        Gets nearby faults within circuit
        :return: Collection of plgis.models.Fault
        '''
        faults = {f.id: f.get_position().distance(self.position) for f in
                  Fault.objects.filter(address__circuit=str(self.circuit.id))}
        k_nearest = dict(sorted(faults.items(), key=itemgetter(1))[:k])
        return Fault.objects.filter(id__in=list(k_nearest.keys()))


@receiver(post_delete, sender=Image)  # TODO: Make it work
def delete_image_from_fs(sender, instance, created, **kwargs):
    print('delete')
    print(80 * '*')
    os.remove(instance.path)


class Fault(models.Model):
    address = JSONField(default=dict) # Check the JSON example on the bottom of this file
    component = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    severity = models.IntegerField()
    comment = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.component}-{self.type}-[{self.severity}]'

    def get_position(self):
        '''
        Since the fault does not have any coordinates associated with it,
        we gotta rely on the marking, which get coordinates through the image
        position. However the fault could be marked on several images,
        so this function takes a centroid of the associated images
        '''
        img_pos = [m.image.position for m in Marking.objects.filter(fault__id=self.id)]
        return MultiPoint(img_pos).centroid

    @staticmethod
    def get_recent_faults(circuit_id=None, k=10):
        # convert to set to remove duplicate values. (several marking point to the same fault)
        if circuit_id:
            return set([
                m.fault for m in Marking.objects
                .filter(fault__address__circuit=str(circuit_id))
                .order_by('-date_updated')
                ][:k])
        else:
            return set([
                m.fault for m in Marking.objects.all()
                .order_by('-date_updated')
                ][:k])

    def get_images(self):
        return [m.image for m in Marking.objects.filter(fault=self)]

    def get_marks(self):
        return Marking.objects.filter(fault=self)

    def get_macro_type(self):
        if 'bundle' in self.address:
            return 'Span Field'
        else:
            return 'Tower'

class Marking(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    fault = models.ForeignKey(Fault, on_delete=models.CASCADE)
    marking = models.CharField(max_length=100)

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.fault}@{self.image.get_fname()}'

    @staticmethod
    def get_marks_in_circuit(circuit_id):
        return Marking.objects.filter(fault__address__circuit=circuit_id)

    @staticmethod
    def get_nearby_marks(pos, k=10):
        imgs = {m.id: m.image.position.distance(pos) for m in Marking.objects.all()}
        k_nearest = dict(sorted(imgs.items(), key=itemgetter(1))[:k])
        return Marking.objects.filter(id__in=list(k_nearest.keys()))

    @staticmethod
    def get_recent_marks(circuit_id=None):
        if circuit_id:
            return Marking.objects.filter(fault__address__circuit=circuit_id).order_by('-date_updated')
        else:
            return Marking.objects.all().order_by('-date_updated')

########################################################################################################################
################################################### Example JSONs ######################################################
########################################################################################################################


################################################# Tower.traverses: #####################################################
# {
#   "traverse00": {
#     "number": 0,
#     "bundles": {
#       "M-0": {
#         "side": "M",
#         "cables": {
#           "count": "1",
#           "config": "S"
#         },
#         "position": "0",
#         "components": [           /* Content of the components array is not regulated*/
#           "Marker Balls"
#         ]
#       }
#     }
#   },
#   "traverse01": {
#     "number": 1,
#     "bundles": {
#       "L-1": {
#         "side": "L",
#         "cables": {
#           "count": "4",
#           "config": "Q"
#         },
#         "position": "1",
#         "components": [
#           "Vibration Dampers",
#           "Insulator",
#           "Fitting"
#         ]
#       },
#       "R-1": {
#         "side": "R",
#         "cables": {
#           "count": "4",
#           "config": "Q"
#         },
#         "position": "1",
#         "components": [
#           "Vibration Dampers",
#           "Insulator",
#           "Fitting"
#         ]
#       }
#     }
#   }
# }

################################################### Image.properties ###################################################
# {
#     "type": "tower",
#     "section": "T_01"
# }
#
# {
#     "type": "span_field",
#     "section": "SF-01_02"
# }

################################################## Fault.address ########################################################
# {
#    "side":"M",
#    "cable":"1",
#    "bundle":"T0_M_0",
#    "circuit":"25",
#    "section":"SF-01_02",
#    "traverse":"0"
# }
#
# {
#    "side":"L",
#    "circuit":"25",
#    "section":"T_01",
#    "traverse":"1"
# }
