from copy import deepcopy

from django.contrib import admin, messages
from django.contrib.admin.options import BaseModelAdmin, InlineModelAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, path
from django.utils.safestring import mark_safe

from .admin_utils import remove_from_fieldsets
from .filters import SearchInFilter
from .forms import EnhancedBaseInlineFormSet
from .utils import ifilter


class EnhancedAdminInlineMixin(InlineModelAdmin):
    select2_inlines_fields = []
    default_field_queryset = dict()
    limit_field_queryset_model_fields = dict()
    limit_saved_queryset_value_fields = []
    formset = EnhancedBaseInlineFormSet

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.limit_saved_queryset_value_fields = self.limit_saved_queryset_value_fields
        formset.default_field_queryset = self.default_field_queryset
        formset.limit_field_queryset_model_fields = self.limit_field_queryset_model_fields
        return formset

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in self.select2_inlines_fields:
            field.widget.attrs['class'] = 'inline-select2'
        return field


class EnhancedBaseAdminMixin(BaseModelAdmin):
    user_field = 'created_by'
    only_delete_owned = False

    def has_delete_permission(self, request, obj=None):
        if self.only_delete_owned and not request.user.has_perm('user.is_admin'):
            if not (obj and getattr(obj, self.user_field).id == request.user.id):
                return False
        return super(EnhancedBaseAdminMixin, self).has_delete_permission(request, obj)


class AjaxActionMixin:
    admin_site = None
    """
        List of tuples:
        ('field_name', dict(btn_text, btn_class, additional_html, callback, short_desc))
    """
    ajax_action_fields = []

    def get_readonly_fields(self, request, obj=None):
        return list(super().get_readonly_fields(request, obj)) + [x[0] for x in self.get_ajax_action_fields()]

    def get_ajax_action_fields(self):
        return self.ajax_action_fields

    def get_callback_key(self, name):
        return f'{self.__class__.__name__}_{name}'

    def register_callback(self, name, callback):
        if not hasattr(self.admin_site, 'ajax_handler_callback_params'):
            self.admin_site.ajax_handler_callback_params = {}
        param_key = self.get_callback_key(name)
        if not self.admin_site.ajax_handler_callback_params.get(param_key):
            self.admin_site.ajax_handler_callback_params[param_key] = (self, callback)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, config in self.get_ajax_action_fields():
            btn_text = config.get('btn_text', 'Button')
            btn_class = config.get('btn_class', 'btn btn-warning')

            @mark_safe
            def func(instance):
                if not instance.id:
                    return ''
                url = reverse('django_reusable:ajax_callback_handler',
                              args=(instance.pk, self.get_callback_key(name)))
                return (f'<button class="{btn_class} ajax-action-btn" data-url="{url}">{btn_text}</button>' +
                        config.get('additional_html', ''))

            func.short_description = config.get('short_desc', btn_text)
            func.__name__ = name
            setattr(self, func.__name__, func)

            self.register_callback(name, config['callback'])


class EnhancedAdminMixin(admin.ModelAdmin, EnhancedBaseAdminMixin):
    default_filters = []
    search_in_choices = []
    """
        List of tuples:
        ('field_name', lambda instance: instance.field.name, optional short_desc)
    """
    custom_fields = []
    """
        List of tuples:
        ('name', dict(btn_text, btn_class, stay_on_page, callback))
    """
    extra_change_form_buttons = []
    """
        List of tuples:
        (url, dict(link_text, link_class, new_tab, user_passes_test))
    """
    extra_changelist_links = []
    """
        List of tuples:
        ('name', dict(btn_text, btn_class, callback, short_desc, custom_redirect))
        Note: callback is called with args (instance)
    """
    action_links = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.search_in_choices:
            if not ifilter(lambda x: 'SearchInFilter' in str(x), self.list_filter):
                filter_class = type('%sSearchInFilter' % self.__class__.__name__, (SearchInFilter,),
                                    {'lookup_choices': sorted(self.search_in_choices, key=lambda x: x[1])})
                self.list_filter.insert(0, filter_class)
            self.base_search_fields = map(lambda xy: xy[0], self.search_in_choices)

        for f in self.custom_fields:
            func = f[1]
            func.allow_tags = True
            if len(f) > 2:
                func.short_description = f[2]
            func.__name__ = f[0]
            setattr(self, func.__name__, func)

        def get_action_link_fn(name, attrs):
            func = lambda instance: mark_safe(
                '<a class="btn {0}" href="{1}">{2}</a>'.format(
                    attrs.get('btn_class', ''),
                    reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_action_view_{name}',
                            args=(instance.id,)),
                    attrs.get('btn_text', ''),
                ))
            func.allow_tags = True
            if 'short_desc' in attrs:
                func.short_description = attrs['short_desc']
            func.__name__ = name
            return func

        for name, attrs in self.action_links:
            if 'callback' not in attrs:
                continue
            func = get_action_link_fn(name, attrs)
            setattr(self, func.__name__, func)

    def get_search_fields(self, request):
        search_fields = deepcopy(self.search_fields)
        if self.search_in_choices:
            search_fields = [request.GET.get(SearchInFilter.parameter_name)] if request.GET.get(
                SearchInFilter.parameter_name) else (search_fields or self.base_search_fields)
        return search_fields

    def hide_save_buttons(self, request, object_id):
        """
        Hook method to hide save buttons and disable POST on some conditions.

        :param request: HttpRequest object
        :param object_id: Object ID of the current change page
        :return: True to hide save buttons, False otherwise
        """
        return False

    def get_changelist_extra_context(self, request):
        return {}

    def custom_changelist_actions(self, request):
        pass

    def _add_extra_change_form_buttons(self, request, extra_context):
        extra_context.update(
            extra_submit_buttons=[
                (f'__{name}', config.get('btn_class', 'btn-primary'), config.get('btn_text', 'Button'))
                for (name, config) in self.extra_change_form_buttons
                if config.get('user_passes_test', lambda u: True)(request.user)
            ]
        )

    def _handle_extra_change_form_buttons(self, request, object_id):
        for (name, config) in self.extra_change_form_buttons:
            if f'__{name}' not in request.POST:
                continue
            callback = config.get('callback')
            if callback:
                r = callback(self, request, object_id)
                if r:
                    messages.info(request, r)
            if config.get('stay_on_page', False):
                return HttpResponseRedirect(self.model.get_change_url(object_id))
            break
        return None

    def _add_extra_changelist_links(self, request, extra_context):
        extra_context.update(
            extra_links=[
                (url,
                 config.get('link_class', 'btn-link'),
                 config.get('link_text', 'Link'),
                 config.get('new_tab', False))
                for (url, config) in self.get_extra_changelist_links(request)
                if config.get('user_passes_test', lambda u: True)(request.user)
            ]
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        self.custom_changelist_actions(request)
        self._add_extra_changelist_links(request, extra_context)
        if self.default_filters:
            try:
                test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])
                if test and test[-1] and not test[-1].startswith('?'):
                    url = reverse('admin:%s_%s_changelist' % (self.opts.app_label, self.opts.model_name))
                    filters = []
                    for f in self.default_filters:
                        key = f.split('=')[0]
                        if key not in request.GET:
                            filters.append(f)
                    if filters:
                        return HttpResponseRedirect("%s?%s" % (url, "&".join(filters)))
            except:
                pass
        extra_context.update(self.get_changelist_extra_context(request) or {})
        return super(EnhancedAdminMixin, self).changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(
            hide_save_buttons=self.hide_save_buttons(request, object_id)
        )
        self._add_extra_change_form_buttons(request, extra_context)
        if request.method == 'POST' and extra_context['hide_save_buttons']:
            raise PermissionDenied()
        response = super().change_view(request, object_id, form_url, extra_context)
        if request.method == 'POST':
            return self._handle_extra_change_form_buttons(request, object_id) or response
        return response

    def remove_inline_instances(self, inline_instances, *inlines_to_remove):
        to_remove = set()
        for inline_class in inlines_to_remove:
            inline = inline_class(self.model, self.admin_site)
            for index, i in enumerate(inline_instances):
                if type(inline) == type(i):
                    to_remove.add(i)
        for inline in to_remove:
            if inline in inline_instances:
                inline_instances.remove(inline)

    def get_readonly_fields(self, request, obj=None):
        return (list(super().get_readonly_fields(request, obj)) +
                [x[0] for x in self.custom_fields] +
                [x[0] for x in self.action_links])

    def get_extra_changelist_links(self, request):
        return self.extra_changelist_links

    def get_fieldset_section_exclusions(self, request, obj):
        return []

    def get_fieldset_field_exclusions(self, request, obj):
        return []

    def get_fieldsets(self, request, obj=None):
        original_fieldsets = super().get_fieldsets(request, obj)
        field_exclusions = self.get_fieldset_field_exclusions(request, obj)
        section_exclusions = self.get_fieldset_section_exclusions(request, obj)
        if not field_exclusions and not section_exclusions:
            return original_fieldsets
        fieldsets = deepcopy(original_fieldsets)
        if section_exclusions:
            fieldsets = [(title, attributes) for title, attributes in fieldsets if title not in section_exclusions]
        if field_exclusions:
            remove_from_fieldsets(fieldsets, field_exclusions)
        return fieldsets

    def get_urls(self):
        urls = super().get_urls()
        my_urls = []

        def get_action_link_view(_view_name, _attrs):
            def action_link_view(request, pk):
                obj = self.model.objects.get(id=pk)
                response = _attrs['callback'](obj)
                if _attrs.get('custom_redirect'):
                    return response
                return redirect(request.META.get('HTTP_REFERER'))

            action_link_view.__name__ = _view_name
            return action_link_view

        for (name, attrs) in self.action_links:
            if 'callback' not in attrs:
                continue
            view_name = f'{self.model._meta.app_label}_{self.model._meta.model_name}_action_view_{name}'

            my_urls.append(path(f'<path:pk>/action-link/{name}/',
                                self.admin_site.admin_view(get_action_link_view(view_name, attrs)),
                                name=view_name))
        return my_urls + urls


class ReadonlyAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return self.get_list_display(request)

    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name
                             not in ['id', 'created', 'modified']]
        super().__init__(model, admin_site)
