import traceback

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe

from django_reusable.utils import get_property


class GenericRelationMixin(models.Model):
    @property
    def this_content_object(self):
        return type(self).objects.filter(content_type=self.content_type, object_id=self.object_id)

    @property
    def this_content_type(self):
        return type(self).objects.filter(content_type=self.content_type)

    @classmethod
    def for_object(cls, obj):
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(obj)), object_id=obj.id)

    @classmethod
    def for_objects(cls, objs):
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(objs[0])),
                                  object_id__in=[obj.id for obj in objs]) if objs else None

    @classmethod
    def for_object_type(cls, obj):
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(type(obj)))

    @classmethod
    def for_model(cls, model):
        return cls.objects.filter(content_type=ContentType.objects.get_for_model(model))

    @staticmethod
    def model_content_type(model):
        return ContentType.objects.get_for_model(model)

    @staticmethod
    def obj_content_type(obj):
        return ContentType.objects.get_for_model(type(obj))

    class Meta:
        abstract = True


class ModelUtilsMixin:

    @classmethod
    def get_add_url_name(cls, site='admin'):
        return '%s:%s_%s_add' % (site, cls._meta.app_label, cls._meta.model_name)

    @classmethod
    def get_add_url(cls, site='admin'):
        return reverse(cls.get_add_url_name(site))

    @classmethod
    def get_changelist_url_name(cls, site='admin'):
        return '%s:%s_%s_changelist' % (site, cls._meta.app_label, cls._meta.model_name)

    @classmethod
    def get_changelist_url(cls, site='admin'):
        return reverse(cls.get_changelist_url_name(site))

    @classmethod
    def get_change_url_name(cls, site='admin'):
        return '%s:%s_%s_change' % (site, cls._meta.app_label, cls._meta.model_name)

    def get_change_url_for_object(self, site='admin'):
        return reverse(self.get_change_url_name(site), args=[self.pk])

    @classmethod
    def get_change_url(cls, pk, site='admin'):
        return reverse(cls.get_change_url_name(site), args=[pk])

    def get_obj_change_url(self, site='admin'):
        return self.__class__.get_change_url(self.pk, site)

    @classmethod
    def get_delete_url_name(cls, site='admin'):
        return '%s:%s_%s_delete' % (site, cls._meta.app_label, cls._meta.model_name)

    @classmethod
    def get_delete_url(cls, pk, site='admin'):
        return reverse(cls.get_delete_url_name(site), args=[pk])

    def get_obj_delete_url(self, site='admin'):
        return self.__class__.get_delete_url(self.pk, site)

    @property
    def change_link(self):
        if self.pk:
            try:
                return mark_safe(u'<a href="{w}" class="admin-edit-link">Details</a>'.format(
                    w=self.__class__.get_change_url(self.pk)))
            except NoReverseMatch:
                return None
        else:
            return None

    @property
    def original_obj(self):
        if not hasattr(self, '_orig_obj'):
            self._orig_obj = self.__class__.objects.get(id=self.pk) if self.pk else None
        return self._orig_obj

    def get_property(self, name, fn):
        return get_property(self, name, fn)

    class Meta:
        abstract = True


class TimeStampedModelOnly(models.Model, ModelUtilsMixin):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MonitorChangeMixin:
    """
        List of tuples:
        ('field_name', dict(callback: lambda (self, old_value, new_value)))
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
    class Meta:
        abstract = True
