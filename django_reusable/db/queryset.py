from django.db import models
from django.dispatch import Signal

post_update = Signal()
"""Signal sent after ``CustomQuerySet.update()`` completes.

Provides ``sender`` (the model class), the update kwargs, and ``objs``
(list of objects that were updated, fetched before the update).
"""

post_bulk_create = Signal()
"""Signal sent after ``CustomManager.bulk_create()`` completes.

Provides ``sender`` (the model class), ``objs`` (created objects),
and ``batch_size``.
"""


class CustomQuerySet(models.query.QuerySet):
    """QuerySet subclass that sends a ``post_update`` signal after ``.update()`` calls."""

    def update(self, **kwargs):
        # fetching objects to be updated before update happens, since update might affect the queryset
        objs = list(self)
        super(CustomQuerySet, self).update(**kwargs)
        kwargs.update({'objs': objs})
        post_update.send(sender=self.model, **kwargs)


class CustomManager(models.Manager):
    """Manager that uses ``CustomQuerySet`` and sends ``post_bulk_create`` after bulk creates."""

    def get_queryset(self):
        return CustomQuerySet(self.model, using=self._db)

    def bulk_create(self, objs, batch_size=None):
        super(CustomManager, self).bulk_create(objs, batch_size)
        kwargs = {'objs': objs, 'batch_size': batch_size}
        post_bulk_create.send(sender=self.model, **kwargs)
