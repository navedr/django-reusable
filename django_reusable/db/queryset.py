from django.db import models
from django.dispatch import Signal

# Signal sent after an update operation
post_update = Signal()
# Signal sent after a bulk create operation
post_bulk_create = Signal()


class CustomQuerySet(models.query.QuerySet):
    """
    A custom QuerySet class that sends a signal after an update operation.
    """

    def update(self, **kwargs):
        """
        Updates the records in the queryset and sends a post_update signal.

        Args:
            **kwargs: The fields and values to update.

        Returns:
            int: The number of rows matched by the query.
        """
        # Fetching objects to be updated before update happens, since update might affect the queryset
        objs = list(self)
        super(CustomQuerySet, self).update(**kwargs)
        kwargs.update({'objs': objs})
        post_update.send(sender=self.model, **kwargs)


class CustomManager(models.Manager):
    """
    A custom Manager class that uses CustomQuerySet and sends a signal after a bulk create operation.
    """

    def get_queryset(self):
        """
        Returns a CustomQuerySet instance.

        Returns:
            CustomQuerySet: The custom queryset.
        """
        return CustomQuerySet(self.model, using=self._db)

    def bulk_create(self, objs, batch_size=None):
        """
        Creates the provided list of objects in bulk and sends a post_bulk_create signal.

        Args:
            objs (list): The list of objects to create.
            batch_size (int, optional): The number of objects to create in a single batch. Defaults to None.

        Returns:
            list: The list of created objects.
        """
        super(CustomManager, self).bulk_create(objs, batch_size)
        kwargs = {'objs': objs, 'batch_size': batch_size}
        post_bulk_create.send(sender=self.model, **kwargs)
