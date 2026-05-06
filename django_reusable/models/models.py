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
    """Mixin for models using Django's generic relations (ContentType framework).

    Provides convenience class methods and properties for querying related
    objects through content types without manually constructing ContentType filters.

    Subclasses must define ``content_type`` (ForeignKey to ContentType) and
    ``object_id`` fields, typically via ``GenericForeignKey``.

    Example:
        ```python
        from django.contrib.contenttypes.fields import GenericForeignKey
        from django.contrib.contenttypes.models import ContentType

        class Comment(GenericRelationMixin):
            content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey('content_type', 'object_id')
            text = models.TextField()

        # Query comments for a specific object
        comments = Comment.for_object(my_article)
        ```
    """

    @property
    def content_object_link(self):
        return mark_safe(f'''{self.content_type}: <a target="_blank" 
        href="{self.content_object.get_obj_change_url()}">{self.content_object}</a>''')

    @property
    def this_content_object(self):
        return type(self).objects.filter(content_type=self.content_type, object_id=self.object_id)

    @property
    def this_content_type(self):
        return type(self).objects.filter(content_type=self.content_type)

    @classmethod
    def for_object(cls, obj):
        """Return queryset filtered to a specific object instance.

        Args:
            obj: The model instance to filter by (matches both content type and ID).

        Returns:
            QuerySet of records related to the given object.
        """
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(obj)), object_id=obj.id)

    @classmethod
    def for_objects(cls, objs):
        """Return queryset filtered to multiple object instances of the same type.

        Args:
            objs: List of model instances (must all be the same model type).

        Returns:
            QuerySet of records related to any of the given objects, or None if
            the list is empty.
        """
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(objs[0])),
                                  object_id__in=[obj.id for obj in objs]) if objs else None

    @classmethod
    def for_object_type(cls, obj):
        """Return queryset filtered to all records for an object's model type.

        Args:
            obj: A model instance whose type is used to determine the content type.

        Returns:
            QuerySet of all records matching the content type of the given object.
        """
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(obj)))

    @classmethod
    def for_model(cls, model):
        """Return queryset filtered to all records for a given model class.

        Args:
            model: A Django model class.

        Returns:
            QuerySet of all records matching the content type of the given model.
        """
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(model))

    @staticmethod
    def model_content_type(model):
        return ContentType.objects.get_for_model(model)

    @staticmethod
    def obj_content_type(obj):
        return ContentType.objects.get_for_model(type(obj))

    class Meta:
        abstract = True


class ModelUtilsMixin(models.Model):
    """Mixin providing Django admin URL helpers for model instances and classes.

    Adds class methods and instance methods/properties for generating admin
    URLs (add, change, changelist, delete) without manually constructing
    URL patterns. Also provides ``original_obj`` for comparing field changes
    and a ``change_link`` property for rendering clickable admin links.

    Example:
        ```python
        class Person(ModelUtilsMixin):
            name = models.CharField(max_length=100)

        # Class-level URLs
        Person.get_add_url()           # /admin/myapp/person/add/
        Person.get_changelist_url()    # /admin/myapp/person/
        Person.get_change_url(pk=1)    # /admin/myapp/person/1/change/

        # Instance-level
        person = Person.objects.get(pk=1)
        person.get_obj_change_url()    # /admin/myapp/person/1/change/
        person.change_link             # HTML <a> tag linking to change page
        ```
    """

    @classmethod
    def get_add_url_name(cls, site='admin'):
        return ModelURLs(cls, site).get_add_url_name()

    @classmethod
    def get_add_url(cls, site='admin'):
        return ModelURLs(cls, site).get_add_url()

    @classmethod
    def get_changelist_url_name(cls, site='admin'):
        return ModelURLs(cls, site).get_changelist_url_name()

    @classmethod
    def get_changelist_url(cls, site='admin'):
        return ModelURLs(cls, site).get_changelist_url()

    @classmethod
    def get_change_url_name(cls, site='admin'):
        return ModelURLs(cls, site).get_change_url_name()

    def get_change_url_for_object(self, site='admin'):
        return ModelURLs(self, site, self.pk).get_obj_change_url()

    @classmethod
    def get_change_url(cls, pk, site='admin'):
        return ModelURLs(cls, site, pk).get_obj_change_url()

    def get_obj_change_link_tag(self, text, css_class='', target='', site='admin'):
        return ModelURLs(self, site, self.pk).get_obj_change_link_tag(text, css_class, target)

    def get_obj_change_url(self, site='admin'):
        return ModelURLs(self, site, self.pk).get_obj_change_url()

    @classmethod
    def get_delete_url_name(cls, site='admin'):
        return ModelURLs(cls, site).get_delete_url_name()

    @classmethod
    def get_delete_url(cls, pk, site='admin'):
        return ModelURLs(cls, site, pk).get_obj_delete_url()

    def get_obj_delete_url(self, site='admin'):
        return ModelURLs(self, site, self.pk).get_obj_delete_url()

    @property
    def change_link(self):
        return ModelURLs(self, pk=self.pk).get_change_link()

    @property
    def original_obj(self):
        if not hasattr(self, '_orig_obj'):
            self._orig_obj = self.__class__.objects.get(id=self.pk) if self.pk else None
        return self._orig_obj

    def get_property(self, name, fn):
        return get_property(self, name, fn)

    class Meta:
        abstract = True


class TimeStampedModelOnly(ModelUtilsMixin):
    """Abstract base model with automatic ``created`` and ``modified`` timestamps.

    Inherits admin URL helpers from ``ModelUtilsMixin`` but does not include
    change monitoring. Use ``TimeStampedModel`` if you also need field change
    callbacks.

    Attributes:
        created: Auto-set to the current time when the object is first saved.
        modified: Auto-updated to the current time on every save.

    Example:
        ```python
        class AuditLog(TimeStampedModelOnly):
            action = models.CharField(max_length=200)
        ```
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MonitorChangeMixin:
    """Mixin that fires callbacks when monitored field values change on save.

    Set ``monitor_fields`` to a list of ``(field_name, options)`` tuples.
    Each ``options`` dict may contain a ``callback`` that receives the instance,
    old value, and new value whenever the field changes.

    Requires ``original_obj`` (provided by ``ModelUtilsMixin``) to compare
    pre-save and post-save values.

    Attributes:
        monitor_fields: List of tuples defining which fields to watch and
            their callbacks.

    Example:
        ```python
        class Order(TimeStampedModel):
            status = models.CharField(max_length=20)

            monitor_fields = [
                ('status', {
                    'callback': lambda self, old, new: print(
                        f"Order {self.pk} status: {old} -> {new}"
                    )
                }),
            ]

            def save(self, **kwargs):
                super().save(**kwargs)
                self.notify_changes()
        ```
    """
    monitor_fields = []

    def notify_changes(self):
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
    """Abstract base model with timestamps and field change monitoring.

    Combines ``TimeStampedModelOnly`` (created/modified fields + admin URL helpers)
    with ``MonitorChangeMixin`` (field change callbacks). This is the recommended
    base class for most application models.

    Example:
        ```python
        class Person(TimeStampedModel):
            first_name = models.CharField(max_length=30)
            last_name = models.CharField(max_length=30)
            home_address = USAddressField(blank=True, null=True)
            roles = MultipleChoiceField(
                choices=[('Admin', 'Admin'), ('User', 'User')],
                null=True, blank=True, default=['Guest'],
            )
        ```
    """
    class Meta:
        abstract = True


Page = namedtuple("Page", "has_next, next_num, has_prev, prev_num, items ")


class Error(models.Model):
    """Stores captured exceptions for the ``ExceptionTrackerMiddleware``.

    Each unique exception (identified by hash) is stored once; subsequent
    occurrences increment the ``count`` and update ``last_seen``.
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
        return json.dumps(literal_eval(self.request_data), indent=4)

    @classmethod
    def get_exceptions_per_page(cls, page_number=1):
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
        return cls.objects.get(pk=rhash)

    @classmethod
    def create_or_update_entity(cls, rhash, host, path, method, request_data, exception_name, _traceback):
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
        return cls.objects.filter(pk=rhash).delete()

    def __str__(self):
        return "'%s' '%s' %s" % (self.host, self.path, self.count)

    def __unicode__(self):
        return self.__str__()

    class Meta:
        ordering = ['-last_seen']
