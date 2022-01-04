from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse


# Create your models here.
class Dictionary(models.Model):
    """A model that represents a dictionary. This model implements most of the dictionary interface,
    allowing it to be used like a python dictionary.

    """
    name = models.CharField(max_length=255)

    @staticmethod
    def getDict(name):
        """Get the Dictionary of the given name.

        """
        df = Dictionary.objects.select_related().get(name=name)

        return df

    def __getitem__(self, key):
        """Returns the value of the selected key.

        """
        return self.keyvaluepair_set.get(key=key).value

    def __setitem__(self, key, value):
        """Sets the value of the given key in the Dictionary.

        """
        try:
            kvp = self.keyvaluepair_set.get(key=key)

        except KVP.DoesNotExist:
            KVP.objects.create(container=self, key=key, value=value)

        else:
            kvp.value = value
            kvp.save()

    def __delitem__(self, key):
        """Removed the given key from the Dictionary.

        """
        try:
            kvp = self.keyvaluepair_set.get(key=key)

        except KVP.DoesNotExist:
            raise KeyError

        else:
            kvp.delete()

    def __len__(self):
        """Returns the length of this Dictionary.

        """
        return self.keyvaluepair_set.count()

    def iterkeys(self):
        """Returns an iterator for the keys of this Dictionary.

        """
        return iter(kvp.key for kvp in self.keyvaluepair_set.all())

    def itervalues(self):
        """Returns an iterator for the keys of this Dictionary.

        """
        return iter(kvp.value for kvp in self.keyvaluepair_set.all())

    __iter__ = iterkeys

    def iteritems(self):
        """Returns an iterator over the tuples of this Dictionary.

        """
        return iter((kvp.key, kvp.value) for kvp in self.keyvaluepair_set.all())

    def keys(self):
        """Returns all keys in this Dictionary as a list.

        """
        return [kvp.key for kvp in self.keyvaluepair_set.all()]

    def values(self):
        """Returns all values in this Dictionary as a list.

        """
        return [kvp.value for kvp in self.keyvaluepair_set.all()]

    def items(self):
        """Get a list of tuples of key, value for the items in this Dictionary.
        This is modeled after dict.items().

        """
        return [(kvp.key, kvp.value) for kvp in self.keyvaluepair_set.all()]

    def get(self, key, default=None):
        """Gets the given key from the Dictionary. If the key does not exist, it
        returns default.

        """
        try:
            return self[key]

        except KeyError:
            return default

    def has_key(self, key):
        """Returns true if the Dictionary has the given key, false if not.

        """
        return self.contains(key)

    def contains(self, key):
        """Returns true if the Dictionary has the given key, false if not.

        """
        try:
            self.keyvaluepair_set.get(key=key)
            return True

        except KVP.DoesNotExist:
            return False

    def clear(self):
        """Deletes all keys in the Dictionary.

        """
        self.keyvaluepair_set.all().delete()

    def __unicode__(self):
        """Returns a unicode representation of the Dictionary.

        """
        return str(self.asPyDict())
        # return unicode(self.asPyDict()) #For the record: This method was edited. Changed it so it would let
        # the program execute, dunno if it really does what it's supposed to do. Some legacy issues probably.

    def asPyDict(self):
        """Get a python dictionary that represents this Dictionary object.
        This object is read-only.

        """
        fieldDict = dict()

        for kvp in self.keyvaluepair_set.all():
            fieldDict[kvp.key] = kvp.value

        return fieldDict


class KVP(models.Model):
    """A Key-Value pair with a pointer to the Dictionary that owns it.

    """
    container = models.ForeignKey(Dictionary, on_delete=models.CASCADE, db_index=True)
    key = models.CharField(max_length=240, db_index=True)
    value = models.CharField(max_length=240, db_index=True)


# Macro Components

class Circuit(models.Model):
    identifier = models.CharField(max_length=255)
    voltage = models.IntegerField()
    substation_start = models.CharField(max_length=255, blank=True)
    substation_end = models.CharField(max_length=255, blank=True)
    date_added = models.DateTimeField(auto_created=True)

    FIELDS = {
        'ID': identifier,
        'Voltage': voltage,
        'Start': substation_start,
        'End': substation_end,
        'Date Added': date_added,
    }

    def get_absolute_url(self):
        return reverse('circuit', kwargs={'id': self.pk})

    def __repr__(self):
        return self.identifier

    def __str__(self):
        return self.__repr__()

class Tower(models.Model):
    identifier = models.CharField(max_length=255)
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE)
    type = models.CharField(max_length=255)  # TODO: Choices
    position = models.PointField()

    FIELDS = {
        'ID': identifier,
        'Circuit': circuit,
        'Type': type,
        'Position': position
    }


class SpanField(models.Model):
    tower_start = models.ForeignKey(Tower, related_name='tower_start', on_delete=models.CASCADE)
    tower_end = models.ForeignKey(Tower, related_name='tower_end', on_delete=models.CASCADE)


    # TODO: Autofield identifier: tower_start.identifier
    # TODO: Check tower_end != tower_start @ save()
    @property
    def identifier(self):
        return self.tower_start.identifier + '-' + self.tower_end.identifier

    FIELDS = {
        'ID': identifier,
        'Start': tower_start,
        'End': tower_end
    }

class Macro(models.Model):
    tower = models.ForeignKey(Tower, on_delete=models.CASCADE)
    span_field = models.ForeignKey(SpanField, on_delete=models.CASCADE)

    HEADERS = ('ID', 'Circuit', 'Type', 'Position')

    # TODO: Check that either field is NULL @ save()


class Component(models.Model):
    type = models.CharField(max_length=255)
    macro = models.ForeignKey(Macro, on_delete=models.CASCADE)
    props = models.ForeignKey(Dictionary, on_delete=models.CASCADE)

    FIELDS = {
        'ID':'id',
        'Type': type,
        'Macro': macro,
        'Props': props
    }
