from django.db import models
from django.dispatch import Signal

post_update = Signal()
post_bulk_create = Signal()


class CustomQuerySet(models.query.QuerySet):
    def update(self, **kwargs):
        # fetching objects to be updated before update happens, since update might affect the queryset
        objs = list(self)
        super(CustomQuerySet, self).update(**kwargs)
        kwargs.update({'objs': objs})
        post_update.send(sender=self.model, **kwargs)


class CustomManager(models.Manager):
    def get_queryset(self):
        return CustomQuerySet(self.model, using=self._db)

    def bulk_create(self, objs, batch_size=None):
        super(CustomManager, self).bulk_create(objs, batch_size)
        kwargs = {'objs': objs, 'batch_size': batch_size}
        post_bulk_create.send(sender=self.model, **kwargs)
