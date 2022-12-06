from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

DEFAULT_SITE = 'admin'


class ModelURLs:
    def __init__(self, model, site=DEFAULT_SITE, pk=None):
        self.model = model
        self.app_label, self.model_name = self.model._meta.app_label, self.model._meta.model_name
        self.pk = pk
        self.site = site

    def get_add_url_name(self):
        return '%s:%s_%s_add' % (self.site, self.app_label, self.model_name)

    def get_add_url(self):
        return reverse(self.get_add_url_name())

    def get_changelist_url_name(self):
        return '%s:%s_%s_changelist' % (self.site, self.app_label, self.model_name)

    def get_changelist_url(self):
        return reverse(self.get_changelist_url_name())

    def get_change_url_name(self):
        return '%s:%s_%s_change' % (self.site, self.app_label, self.model_name)

    def _get_change_url(self, pk):
        return reverse(self.get_change_url_name(), args=[pk])

    def get_obj_change_link_tag(self, text, css_class='', target=''):
        return f'<a target="{target}" class="{css_class}" href="{self.get_obj_change_url()}">{text}</a>'

    def get_obj_change_url(self):
        return self._get_change_url(self.pk)

    def get_delete_url_name(self):
        return '%s:%s_%s_delete' % (self.site, self.app_label, self.model_name)

    def _get_delete_url(self, pk):
        return reverse(self.get_delete_url_name(), args=[pk])

    def get_obj_delete_url(self):
        return self._get_delete_url(self.pk)

    def get_change_link(self):
        if self.pk:
            try:
                return mark_safe(u'<a href="{w}" class="admin-edit-link">Details</a>'.format(
                    w=self.get_obj_change_url()))
            except NoReverseMatch:
                pass
        return None
