import json
import traceback
from ast import literal_eval
from collections import namedtuple

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from django_reusable.admin.urls import ModelURLs
from django_reusable.utils import get_property


class GenericRelationMixin(models.Model):
    """
    A mixin to provide generic relation functionalities.
    """

    @property
    def content_object_link(self):
        """
        Returns a link to the content object.

        Returns:
            str: The HTML link to the content object.
        """
        return mark_safe(f'''{self.content_type}: <a target="_blank" 
                        href="{self.content_object.get_obj_change_url()}">{self.content_object}</a>''')

    @property
    def this_content_object(self):
        """
        Returns the queryset for the current content object.

        Returns:
            QuerySet: The queryset for the current content object.
        """
        return type(self).objects.filter(content_type=self.content_type, object_id=self.object_id)

    @property
    def this_content_type(self):
        """
        Returns the queryset for the current content type.

        Returns:
            QuerySet: The queryset for the current content type.
        """
        return type(self).objects.filter(content_type=self.content_type)

    @classmethod
    def for_object(cls, obj):
        """
        Returns the queryset for a specific object.

        Args:
            obj (Model): The object to filter by.

        Returns:
            QuerySet: The queryset for the specific object.
        """
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(obj)), object_id=obj.id)

    @classmethod
    def for_objects(cls, objs):
        """
        Returns the queryset for a list of objects.

        Args:
            objs (list): The list of objects to filter by.

        Returns:
            QuerySet: The queryset for the list of objects.
        """
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(objs[0])),
                                  object_id__in=[obj.id for obj in objs]) if objs else None

    @classmethod
    def for_object_type(cls, obj):
        """
        Returns the queryset for a specific object type.

        Args:
            obj (Model): The object type to filter by.

        Returns:
            QuerySet: The queryset for the specific object type.
        """
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(obj)))

    @classmethod
    def for_model(cls, model):
        """
        Returns the queryset for a specific model.

        Args:
            model (Model): The model to filter by.

        Returns:
            QuerySet: The queryset for the specific model.
        """
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(model))

    @staticmethod
    def model_content_type(model):
        """
        Returns the content type for a specific model.

        Args:
            model (Model): The model to get the content type for.

        Returns:
            ContentType: The content type for the model.
        """
        return ContentType.objects.get_for_model(model)

    @staticmethod
    def obj_content_type(obj):
        """
        Returns the content type for a specific object.

        Args:
            obj (Model): The object to get the content type for.

        Returns:
            ContentType: The content type for the object.
        """
        return ContentType.objects.get_for_model(type(obj))

    class Meta:
        abstract = True


class ModelUtilsMixin:
    """
    A mixin to provide utility methods for models.
    """

    @classmethod
    def get_add_url_name(cls, site='admin'):
        """
        Returns the URL name for adding a new object.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL name for adding a new object.
        """
        return ModelURLs(cls, site).get_add_url_name()

    @classmethod
    def get_add_url(cls, site='admin'):
        """
        Returns the URL for adding a new object.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL for adding a new object.
        """
        return ModelURLs(cls, site).get_add_url()

    @classmethod
    def get_changelist_url_name(cls, site='admin'):
        """
        Returns the URL name for the changelist view.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL name for the changelist view.
        """
        return ModelURLs(cls, site).get_changelist_url_name()

    @classmethod
    def get_changelist_url(cls, site='admin'):
        """
        Returns the URL for the changelist view.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL for the changelist view.
        """
        return ModelURLs(cls, site).get_changelist_url()

    @classmethod
    def get_change_url_name(cls, site='admin'):
        """
        Returns the URL name for the change view.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL name for the change view.
        """
        return ModelURLs(cls, site).get_change_url_name()

    def get_change_url_for_object(self, site='admin'):
        """
        Returns the URL for changing the current object.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL for changing the current object.
        """
        return ModelURLs(self, site, self.pk).get_obj_change_url()

    @classmethod
    def get_change_url(cls, pk, site='admin'):
        """
        Returns the URL for changing an object by primary key.

        Args:
            pk (int): The primary key of the object.
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL for changing the object.
        """
        return ModelURLs(cls, site, pk).get_obj_change_url()

    def get_obj_change_link_tag(self, text, css_class='', target='', site='admin'):
        """
        Returns an HTML link tag for changing the current object.

        Args:
            text (str): The link text.
            css_class (str, optional): The CSS class for the link. Defaults to ''.
            target (str, optional): The target attribute for the link. Defaults to ''.
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The HTML link tag.
        """
        return ModelURLs(self, site, self.pk).get_obj_change_link_tag(text, css_class, target)

    def get_obj_change_url(self, site='admin'):
        """
        Returns the URL for changing the current object.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL for changing the current object.
        """
        return ModelURLs(self, site, self.pk).get_obj_change_url()

    @classmethod
    def get_delete_url_name(cls, site='admin'):
        """
        Returns the URL name for deleting an object.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL name for deleting an object.
        """
        return ModelURLs(cls, site).get_delete_url_name()

    @classmethod
    def get_delete_url(cls, pk, site='admin'):
        """
        Returns the URL for deleting an object by primary key.

        Args:
            pk (int): The primary key of the object.
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL for deleting the object.
        """
        return ModelURLs(cls, site, pk).get_obj_delete_url()

    def get_obj_delete_url(self, site='admin'):
        """
        Returns the URL for deleting the current object.

        Args:
            site (str, optional): The site name. Defaults to 'admin'.

        Returns:
            str: The URL for deleting the current object.
        """
        return ModelURLs(self, site, self.pk).get_obj_delete_url()

    @property
    def change_link(self):
        """
        Returns an HTML link for changing the current object.

        Returns:
            str: The HTML link for changing the current object.
        """
        return ModelURLs(self, pk=self.pk).get_change_link()

    @property
    def original_obj(self):
        """
        Returns the original object before any changes.

        Returns:
            Model: The original object.
        """
        if not hasattr(self, '_orig_obj'):
            self._orig_obj = self.__class__.objects.get(id=self.pk) if self.pk else None
        return self._orig_obj

    def get_property(self, name, fn):
        """
        Gets a property value, setting it with a function if it does not exist.

        Args:
            name (str): The name of the property.
            fn (function): The function to set the property if it does not exist.

        Returns:
            any: The property value.
        """
        return get_property(self, name, fn)

    class Meta:
        abstract = True


class TimeStampedModelOnly(models.Model, ModelUtilsMixin):
    """
    An abstract base class model that provides self-updating 'created' and 'modified' fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MonitorChangeMixin:
    """
    A mixin to monitor changes in specified fields and trigger callbacks.

    Attributes:
        monitor_fields (list): A list of tuples containing field names and callback options.
    """

    monitor_fields = []

    def notify_changes(self):
        """
        Notifies changes in monitored fields by triggering the specified callbacks.
        """
        try:
            for field, options in self.monitor_fields:
                if not options:
                    continue
                old_value = getattr(self.original_obj, field) if self.original_obj else None
                new_value = getattr(self, field)
                if old_value != new_value:
                    callback = options.get('callback', None)
                    if callback:
                        callback(self, old_value, new_value)
        except:
            traceback.print_exc()

    class Meta:
        abstract = True


class TimeStampedModel(TimeStampedModelOnly, MonitorChangeMixin):
    """
    An abstract base class model that provides self-updating 'created' and 'modified' fields and monitors changes.
    """

    class Meta:
        abstract = True


Page = namedtuple("Page", "has_next, next_num, has_prev, prev_num, items ")


class Error(models.Model):
    """
    A model to store error information.

    Attributes:
        hash (str): The hash of the error.
        host (str): The host where the error occurred.
        path (str): The path where the error occurred.
        method (str): The HTTP method used.
        request_data (str): The request data.
        exception_name (str): The name of the exception.
        traceback (str): The traceback of the error.
        count (int): The count of occurrences.
        created_on (datetime): The creation timestamp.
        last_seen (datetime): The last seen timestamp.
    """

    hash = models.CharField(max_length=64, primary_key=True)
    host = models.CharField(max_length=1024)
    path = models.CharField(max_length=4096)
    method = models.CharField(max_length=64)
    request_data = models.TextField()
    exception_name = models.CharField(max_length=256)
    traceback = models.TextField()
    count = models.IntegerField(default=0)
    created_on = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(auto_now=True, db_index=True)

    @property
    def request_data_json(self):
        """
        Returns the request data as a formatted JSON string.

        Returns:
            str: The formatted JSON string of the request data.
        """
        return json.dumps(literal_eval(self.request_data), indent=4)

    @classmethod
    def get_exceptions_per_page(cls, page_number=1):
        """
        Returns a paginated list of exceptions.

        Args:
            page_number (int, optional): The page number. Defaults to 1.

        Returns:
            Page: A namedtuple containing pagination information and the list of exceptions.
        """
        records = cls.objects.all()
        paginator = Paginator(records, 25)
        try:
            page = paginator.page(page_number)
            return Page(page.has_next(),
                        page.next_page_number() if page.has_next() else None,
                        page.has_previous(),
                        page.previous_page_number() if page.has_previous() else None,
                        page.object_list)
        except EmptyPage:
            return Page(False, None, True, paginator.num_pages, [])

    @classmethod
    def get_entity(cls, rhash):
        """
        Returns an error entity by hash.

        Args:
            rhash (str): The hash of the error.

        Returns:
            Error: The error entity.
        """
        return cls.objects.get(pk=rhash)

    @classmethod
    def create_or_update_entity(cls, rhash, host, path, method, request_data, exception_name, _traceback):
        """
        Creates or updates an error entity.

        Args:
            rhash (str): The hash of the error.
            host (str): The host where the error occurred.
            path (str): The path where the error occurred.
            method (str): The HTTP method used.
            request_data (str): The request data.
            exception_name (str): The name of the exception.
            _traceback (str): The traceback of the error.
        """
        try:
            obj, created = cls.objects.get_or_create(hash=rhash)
            if created:
                obj.host, obj.path, obj.method, obj.request_data, obj.exception_name, obj.traceback = \
                    host, path, method, request_data, exception_name, _traceback
                obj.count = 1
                obj.save()
            else:
                obj.count += 1
                obj.last_seen = now()
                obj.save(update_fields=['count', 'last_seen'])
        except:
            traceback.print_exc()

    @classmethod
    def delete_entity(cls, rhash):
        """
        Deletes an error entity by hash.

        Args:
            rhash (str): The hash of the error.

        Returns:
            int: The number of deleted entities.
        """
        return cls.objects.filter(pk=rhash).delete()

    def __str__(self):
        """
        Returns a string representation of the error.

        Returns:
            str: The string representation of the error.
        """
        return "'%s' '%s' %s" % (self.host, self.path, self.count)

    def __unicode__(self):
        """
        Returns a unicode string representation of the error.

        Returns:
            str: The unicode string representation of the error.
        """
        return self.__str__()

    class Meta:
        ordering = ['-last_seen']
