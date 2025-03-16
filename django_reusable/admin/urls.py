from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

DEFAULT_SITE = 'admin'


class ModelURLs:
    """
    A utility class to generate URLs for Django admin models.

    Attributes:
        model (Model): The Django model class.
        app_label (str): The app label of the model.
        model_name (str): The name of the model.
        pk (int, optional): The primary key of the model instance. Defaults to None.
        site (str): The admin site name. Defaults to 'admin'.
    """

    def __init__(self, model, site=DEFAULT_SITE, pk=None):
        """
        Initializes the ModelURLs instance.

        Args:
            model (Model): The Django model class.
            site (str, optional): The admin site name. Defaults to 'admin'.
            pk (int, optional): The primary key of the model instance. Defaults to None.
        """
        self.model = model
        self.app_label, self.model_name = self.model._meta.app_label, self.model._meta.model_name
        self.pk = pk
        self.site = site

    def get_add_url_name(self):
        """
        Returns the URL name for adding a new model instance.

        Returns:
            str: The URL name for adding a new model instance.
        """
        return '%s:%s_%s_add' % (self.site, self.app_label, self.model_name)

    def get_add_url(self):
        """
        Returns the URL for adding a new model instance.

        Returns:
            str: The URL for adding a new model instance.
        """
        return reverse(self.get_add_url_name())

    def get_changelist_url_name(self):
        """
        Returns the URL name for the model changelist.

        Returns:
            str: The URL name for the model changelist.
        """
        return '%s:%s_%s_changelist' % (self.site, self.app_label, self.model_name)

    def get_changelist_url(self):
        """
        Returns the URL for the model changelist.

        Returns:
            str: The URL for the model changelist.
        """
        return reverse(self.get_changelist_url_name())

    def get_change_url_name(self):
        """
        Returns the URL name for changing a model instance.

        Returns:
            str: The URL name for changing a model instance.
        """
        return '%s:%s_%s_change' % (self.site, self.app_label, self.model_name)

    def _get_change_url(self, pk):
        """
        Returns the URL for changing a specific model instance.

        Args:
            pk (int): The primary key of the model instance.

        Returns:
            str: The URL for changing the model instance.
        """
        return reverse(self.get_change_url_name(), args=[pk])

    def get_obj_change_link_tag(self, text, css_class='', target=''):
        """
        Returns an HTML link tag for changing the model instance.

        Args:
            text (str): The link text.
            css_class (str, optional): The CSS class for the link. Defaults to ''.
            target (str, optional): The target attribute for the link. Defaults to ''.

        Returns:
            str: The HTML link tag for changing the model instance.
        """
        return f'<a target="{target}" class="{css_class}" href="{self.get_obj_change_url()}">{text}</a>'

    def get_obj_change_url(self):
        """
        Returns the URL for changing the current model instance.

        Returns:
            str: The URL for changing the current model instance.
        """
        return self._get_change_url(self.pk)

    def get_delete_url_name(self):
        """
        Returns the URL name for deleting a model instance.

        Returns:
            str: The URL name for deleting a model instance.
        """
        return '%s:%s_%s_delete' % (self.site, self.app_label, self.model_name)

    def _get_delete_url(self, pk):
        """
        Returns the URL for deleting a specific model instance.

        Args:
            pk (int): The primary key of the model instance.

        Returns:
            str: The URL for deleting the model instance.
        """
        return reverse(self.get_delete_url_name(), args=[pk])

    def get_obj_delete_url(self):
        """
        Returns the URL for deleting the current model instance.

        Returns:
            str: The URL for deleting the current model instance.
        """
        return self._get_delete_url(self.pk)

    def get_change_link(self):
        """
        Returns an HTML link for changing the current model instance.

        Returns:
            str or None: The HTML link for changing the current model instance, or None if the URL cannot be reversed.
        """
        if self.pk:
            try:
                return mark_safe(u'<a href="{w}" class="admin-edit-link">Details</a>'.format(
                    w=self.get_obj_change_url()))
            except NoReverseMatch:
                pass
        return None