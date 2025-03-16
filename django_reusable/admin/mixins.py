from copy import deepcopy

from django.contrib import admin, messages
from django.contrib.admin.options import BaseModelAdmin, InlineModelAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, path
from django.utils.safestring import mark_safe

from django_reusable.admin.filters import SearchInFilter
from django_reusable.admin.urls import ModelURLs
from django_reusable.admin.utils import remove_from_fieldsets
from django_reusable.forms.forms import EnhancedBaseInlineFormSet
from django_reusable.utils import ifilter, CustomEncoder, find


class EnhancedAdminInlineMixin(InlineModelAdmin):
    """
    A mixin to enhance Django admin inlines with additional features.

    Attributes:
        auto_update_template (bool): Whether to auto-update the template with extras.
        select2_inlines_fields (list): Fields to use with Select2 widget.
        default_field_queryset (dict): Default queryset for fields.
        limit_field_queryset_model_fields (dict): Model fields to limit the queryset.
        limit_saved_queryset_value_fields (list): Fields to limit the saved queryset values.
        formset (EnhancedBaseInlineFormSet): The formset class to use.
    """
    auto_update_template = True
    select2_inlines_fields = []
    default_field_queryset = dict()
    limit_field_queryset_model_fields = dict()
    limit_saved_queryset_value_fields = []
    formset = EnhancedBaseInlineFormSet

    def get_formset(self, request, obj=None, **kwargs):
        """
        Returns the formset for the inline.

        Args:
            request (HttpRequest): The HTTP request object.
            obj (Model, optional): The parent object. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            BaseInlineFormSet: The formset instance.
        """
        formset = super().get_formset(request, obj, **kwargs)
        formset.limit_saved_queryset_value_fields = self.limit_saved_queryset_value_fields
        formset.default_field_queryset = self.default_field_queryset
        formset.limit_field_queryset_model_fields = self.limit_field_queryset_model_fields
        return formset

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """
        Returns the form field for a database field.

        Args:
            db_field (Field): The database field.
            request (HttpRequest): The HTTP request object.
            **kwargs: Additional keyword arguments.

        Returns:
            Field: The form field instance.
        """
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in self.select2_inlines_fields:
            field.widget.attrs['class'] = 'inline-select2' if not self.auto_update_template else 'dr-inline-select2'
        return field

    @property
    def media(self):
        """
        Returns the media required for the inline.

        Returns:
            Media: The media instance.
        """
        media = super().media
        js = 'django_reusable/js/enhanced-admin-inline.js'
        if hasattr(media, '_js_lists'):
            if media._js_lists:
                media._js_lists[0].append(js)
            else:
                media._js_lists = [[js]]
        else:
            media._js.append(js)
        return media


class EnhancedBaseAdminMixin(BaseModelAdmin):
    """
    A mixin to enhance Django admin with additional base functionalities.

    Attributes:
        user_field (str): The field representing the user who created the object.
        only_delete_owned (bool): Whether to allow deletion only for owned objects.
    """
    user_field = 'created_by'
    only_delete_owned = False

    def has_delete_permission(self, request, obj=None):
        """
        Checks if the user has delete permission for the object.

        Args:
            request (HttpRequest): The HTTP request object.
            obj (Model, optional): The object to check. Defaults to None.

        Returns:
            bool: True if the user has delete permission, False otherwise.
        """
        if self.only_delete_owned and not request.user.has_perm('user.is_admin'):
            if not (obj and getattr(obj, self.user_field).id == request.user.id):
                return False
        return super().has_delete_permission(request, obj)


class AjaxActionMixin:
    """
    A mixin to add AJAX action functionalities to Django admin.

    Attributes:
        ajax_action_fields (list): List of tuples defining AJAX actions.
    """
    ajax_action_fields = []

    def get_ajax_action_fields(self):
        """
        Returns the AJAX action fields.

        Returns:
            list: The list of AJAX action fields.
        """
        return self.ajax_action_fields

    def get_callback_key(self, name):
        """
        Returns the callback key for a given action name.

        Args:
            name (str): The name of the action.

        Returns:
            str: The callback key.
        """
        return f'{self.__class__.__name__}_{name}'

    def ajax_action_callback(self, request, name, object_id=None):
        """
        Handles the AJAX action callback.

        Args:
            request (HttpRequest): The HTTP request object.
            name (str): The name of the action.
            object_id (int, optional): The ID of the object. Defaults to None.

        Returns:
            HttpResponse: The HTTP response with the callback result.
        """
        match = find(lambda x: x[0] == name, self.get_ajax_action_fields())
        if match:
            config = match[1]
            callback = config.get('callback')
            if callback:
                result = callback(self, request, object_id)
                return HttpResponse(result)
        return HttpResponse(f'no callback params defined for {name}')

    def _create_ajax_actions_fn(self):
        """
        Creates AJAX action functions and sets them as attributes.
        """
        info = self.model._meta.app_label, self.model._meta.model_name
        for name, config in self.get_ajax_action_fields():
            btn_text = config.get('btn_text', 'Button')
            btn_class = config.get('btn_class', 'btn btn-warning')

            @mark_safe
            def func(instance):
                """
                Returns the HTML for the AJAX action button.

                Args:
                    instance (Model): The model instance.

                Returns:
                    str: The HTML for the AJAX action button.
                """
                url = reverse('admin:%s_%s-dr-ajax-action' % info, args=(name, instance.id))
                return (f'<button class="{btn_class} dr-ajax-action-btn" data-url="{url}">'
                        f'{btn_text}</button>' +
                        config.get('additional_html', ''))

            func.short_description = config.get('short_desc', btn_text)
            func.__name__ = name
            setattr(self, func.__name__, func)


class ExtraChangelistLinksMixin:
    """
    A mixin to add extra links to the Django admin changelist view.

    Attributes:
        extra_changelist_links (list): List of tuples defining extra changelist links.
    """
    extra_changelist_links = []

    def _get_applicable_extra_changelist_links(self, request):
        """
        Returns the applicable extra changelist links for the request.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            list: The list of applicable extra changelist links.
        """

        def _add_default_values(config):
            config.update(dict(
                link_class=config.get('link_class', 'btn-link'),
                link_text=config.get('link_text', 'Link'),
                new_tab=config.get('new_tab', False)
            ))
            return config

        return [(url, _add_default_values(config)) for (url, config) in self.get_extra_changelist_links(request)
                if config.get('user_passes_test', lambda u: True)(request.user)]

    def _add_extra_changelist_links(self, request, extra_context):
        """
        Adds extra changelist links to the context.

        Args:
            request (HttpRequest): The HTTP request object.
            extra_context (dict): The extra context dictionary.
        """
        extra_context.update(
            extra_links=[
                (url,
                 config['link_class'],
                 config['link_text'],
                 config['new_tab'])
                for (url, config) in self._get_applicable_extra_changelist_links(request)
            ]
        )

    def get_extra_changelist_links(self, request):
        """
        Returns the extra changelist links.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            list: The list of extra changelist links.
        """
        return self.extra_changelist_links

    def _changelist_mixin_js_data(self, request):
        """
        Returns the JavaScript data for the changelist mixin.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            dict: The JavaScript data.
        """
        return dict(
            extra_links=[dict(url=url, config=config) for (url, config) in
                         self._get_applicable_extra_changelist_links(request)]
        )


class ExtraChangeFormButtonsMixin:
    """
    A mixin to add extra buttons to the Django admin change form.

    Attributes:
        extra_change_form_buttons (list): List of tuples defining extra change form buttons.
    """
    extra_change_form_buttons = []

    def _get_applicable_extra_change_form_buttons(self, request, pk):
        """
        Returns the applicable extra change form buttons for the request and object.

        Args:
            request (HttpRequest): The HTTP request object.
            pk (int): The primary key of the object.

        Returns:
            list: The list of applicable extra change form buttons.
        """

        def _add_default_values(config):
            config.update(dict(
                btn_class=config.get('btn_class', 'btn-primary'),
                btn_text=config.get('btn_text', 'Button')
            ))
            return config

        return [
            (name, _add_default_values(config)) for (name, config) in self.extra_change_form_buttons
            if (config.get('user_passes_test', lambda u: True)(request.user) and
                config.get('pk_passes_test', lambda _pk: True)(pk))
        ]

    def _add_extra_change_form_buttons(self, request, pk, extra_context):
        """
        Adds extra change form buttons to the context.

        Args:
            request (HttpRequest): The HTTP request object.
            pk (int): The primary key of the object.
            extra_context (dict): The extra context dictionary.
        """
        extra_context.update(
            extra_submit_buttons=[
                (f'__{name}', config['btn_class'], config['btn_text'])
                for (name, config) in self._get_applicable_extra_change_form_buttons(request, pk)
            ]
        )

    def _handle_extra_change_form_buttons(self, request, object_id):
        """
        Handles the extra change form buttons.

        Args:
            request (HttpRequest): The HTTP request object.
            object_id (int): The primary key of the object.

        Returns:
            HttpResponse: The HTTP response or None.
        """
        for (name, config) in self.extra_change_form_buttons:
            if f'__{name}' not in request.POST:
                continue
            callback = config.get('callback')
            custom_redirect = config.get('custom_redirect', False)
            if callback:
                r = callback(self, request, object_id)
                if r:
                    if custom_redirect:
                        return r
                    else:
                        messages.info(request, r)
            if config.get('stay_on_page', False):
                return HttpResponseRedirect(
                    ModelURLs(self.model, self.admin_site.name, object_id).get_obj_change_url()
                )
            break
        return None

    def _change_form_mixin_js_data(self, request, object_id=None):
        """
        Returns the JavaScript data for the change form mixin.

        Args:
            request (HttpRequest): The HTTP request object.
            object_id (int, optional): The primary key of the object. Defaults to None.

        Returns:
            dict: The JavaScript data.
        """
        return dict(
            object_id=object_id,
            extra_submit_buttons=[
                dict(name=name, config=config)
                for (name, config) in self._get_applicable_extra_change_form_buttons(request, object_id)
            ]
        )


class CustomFieldsMixin:
    """
    A mixin to add custom fields to Django admin.

    Attributes:
        custom_fields (list): List of tuples containing field name, function, and optional short description.
    """
    custom_fields = []

    def _create_custom_fields_fn(self):
        """
        Creates custom field functions and sets them as attributes.
        """
        for f in self.custom_fields:
            func = f[1]
            func.allow_tags = True
            if len(f) > 2:
                func.short_description = f[2]
            func.__name__ = f[0]
            setattr(self, func.__name__, func)


class ActionLinksMixin:
    """
    A mixin to add action links to Django admin.

    Attributes:
        action_links (list): List of tuples containing name and dictionary of button attributes.
    """
    action_links = []

    def _create_action_links_fn(self):
        """
        Creates action link functions and sets them as attributes.
        """

        def get_action_link_fn(name, attrs):
            """
            Returns a function to generate an action link.

            Args:
                name (str): The name of the action.
                attrs (dict): The attributes of the action link.

            Returns:
                function: A function to generate the action link HTML.
            """
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


class EnhancedAdminMixin(admin.ModelAdmin,
                         EnhancedBaseAdminMixin,
                         ExtraChangelistLinksMixin,
                         ExtraChangeFormButtonsMixin,
                         AjaxActionMixin,
                         CustomFieldsMixin,
                         ActionLinksMixin):
    """
    A mixin to enhance Django admin with additional functionalities.

    Attributes:
        auto_update_template (bool): Whether to auto-update the template with extras.
        default_filters (list): List of default filters.
        search_in_choices (list): List of search choices.
    """
    auto_update_template = True
    default_filters = []
    search_in_choices = []

    def _apply_search_in_choices(self):
        """
        Applies search choices to the list filter.
        """
        if self.search_in_choices:
            if not ifilter(lambda x: 'SearchInFilter' in str(x), self.list_filter):
                filter_class = type('%sSearchInFilter' % self.__class__.__name__, (SearchInFilter,),
                                    {'lookup_choices': sorted(self.search_in_choices, key=lambda x: x[1])})
                self.list_filter.insert(0, filter_class)
            self.base_search_fields = map(lambda xy: xy[0], self.search_in_choices)

    def __init__(self, *args, **kwargs):
        """
        Initializes the EnhancedAdminMixin.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._apply_search_in_choices()
        self._create_custom_fields_fn()
        self._create_action_links_fn()
        self._create_ajax_actions_fn()

    def get_search_fields(self, request):
        """
        Returns the search fields for the request.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            list: The list of search fields.
        """
        search_fields = deepcopy(self.search_fields)
        if self.search_in_choices:
            search_fields = [request.GET.get(SearchInFilter.parameter_name)] if request.GET.get(
                SearchInFilter.parameter_name) else (search_fields or self.base_search_fields)
        return search_fields

    def hide_save_buttons(self, request, object_id):
        """
        Hook method to hide save buttons and disable POST on some conditions.

        Args:
            request (HttpRequest): The HTTP request object.
            object_id (int): The object ID of the current change page.

        Returns:
            bool: True to hide save buttons, False otherwise.
        """
        return False

    def get_changelist_extra_context(self, request):
        """
        Returns extra context for the changelist view.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            dict: The extra context dictionary.
        """
        return {}

    def custom_changelist_actions(self, request):
        """
        Custom actions for the changelist view.

        Args:
            request (HttpRequest): The HTTP request object.
        """
        pass

    def _get_default_filters_redirect(self, request):
        """
        Returns a redirect response with default filters if applicable.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponseRedirect: The redirect response with default filters.
        """
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

    def changelist_view(self, request, extra_context=None):
        """
        Renders the changelist view.

        Args:
            request (HttpRequest): The HTTP request object.
            extra_context (dict, optional): The extra context dictionary. Defaults to None.

        Returns:
            HttpResponse: The HTTP response.
        """
        extra_context = extra_context or {}
        self.custom_changelist_actions(request)
        if not self.auto_update_template:
            self._add_extra_changelist_links(request, extra_context)
        default_filters_redirect = self._get_default_filters_redirect(request)
        if default_filters_redirect:
            return default_filters_redirect
        extra_context.update(self.get_changelist_extra_context(request) or {})
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Renders the change view.

        Args:
            request (HttpRequest): The HTTP request object.
            object_id (int): The object ID.
            form_url (str, optional): The form URL. Defaults to ''.
            extra_context (dict, optional): The extra context dictionary. Defaults to None.

        Returns:
            HttpResponse: The HTTP response.
        """
        extra_context = extra_context or {}
        if not self.auto_update_template:
            self._add_extra_change_form_buttons(request, object_id, extra_context)
            extra_context.update(
                hide_save_buttons=self.hide_save_buttons(request, object_id)
            )
        if request.method == 'POST' and self.hide_save_buttons(request, object_id):
            raise PermissionDenied()
        response = super().change_view(request, object_id, form_url, extra_context)
        if request.method == 'POST':
            return self._handle_extra_change_form_buttons(request, object_id) or response
        return response

    def remove_inline_instances(self, inline_instances, *inlines_to_remove):
        """
        Removes specified inline instances.

        Args:
            inline_instances (list): The list of inline instances.
            *inlines_to_remove: The inline classes to remove.
        """
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
        """
        Returns the readonly fields for the request and object.

        Args:
            request (HttpRequest): The HTTP request object.
            obj (Model, optional): The object. Defaults to None.

        Returns:
            list: The list of readonly fields.
        """
        return (list(super().get_readonly_fields(request, obj)) +
                [x[0] for x in self.custom_fields] +
                [x[0] for x in self.action_links] +
                [x[0] for x in self.get_ajax_action_fields()])

    def get_fieldset_section_exclusions(self, request, obj):
        """
        Returns the fieldset section exclusions for the request and object.

        Args:
            request (HttpRequest): The HTTP request object.
            obj (Model): The object.

        Returns:
            list: The list of fieldset section exclusions.
        """
        return []

    def get_fieldset_field_exclusions(self, request, obj):
        """
        Returns the fieldset field exclusions for the request and object.

        Args:
            request (HttpRequest): The HTTP request object.
            obj (Model): The object.

        Returns:
            list: The list of fieldset field exclusions.
        """
        return []

    def get_fieldsets(self, request, obj=None):
        """
        Returns the fieldsets for the request and object.

        Args:
            request (HttpRequest): The HTTP request object.
            obj (Model, optional): The object. Defaults to None.

        Returns:
            list: The list of fieldsets.
        """
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

    def _get_common_mixin_js_data(self):
        """
        Returns common JavaScript data for the mixin.

        Returns:
            dict: The common JavaScript data.
        """
        return dict(
            app=self.model._meta.app_label,
            model=self.model._meta.model_name,
            enabled=self.auto_update_template
        )

    def _changelist_mixin_js_data(self, request):
        """
        Returns JavaScript data for the changelist mixin.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            JsonResponse: The JSON response with the JavaScript data.
        """
        return JsonResponse(dict(
            **self._get_common_mixin_js_data(),
            **super()._changelist_mixin_js_data(request)
        ), encoder=CustomEncoder)

    def _change_form_mixin_js_data(self, request, object_id=None):
        """
        Returns JavaScript data for the change form mixin.

        Args:
            request (HttpRequest): The HTTP request object.
            object_id (int, optional): The object ID. Defaults to None.

        Returns:
            JsonResponse: The JSON response with the JavaScript data.
        """
        return JsonResponse(dict(
            **self._get_common_mixin_js_data(),
            hide_save_buttons=self.hide_save_buttons(request, object_id),
            **super()._change_form_mixin_js_data(request, object_id)
        ), encoder=CustomEncoder)

    def get_urls(self):
        """
        Returns the URLs for the admin view.

        Returns:
            list: The list of URLs.
        """
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        my_urls = [
            path('<path:object_id>/change/dr-admin-mixin-js-data/',
                 self._change_form_mixin_js_data,
                 name='%s_%s-dr-admin-mixin-js-data_change' % info),
            path('add/dr-admin-mixin-js-data/',
                 self._change_form_mixin_js_data,
                 name='%s_%s-dr-admin-mixin-js-data_add' % info),
            path('dr-admin-mixin-js-data/',
                 self._changelist_mixin_js_data,
                 name='%s_%s_dr-admin-mixin-js-data-changelist' % info),
            path('ajax-action/<path:name>/<path:object_id>/',
                 self.ajax_action_callback,
                 name='%s_%s-dr-ajax-action' % info),
        ]

        def get_action_link_view(_view_name, _attrs):
            """
            Returns a view for the action link.

            Args:
                _view_name (str): The view name.
                _attrs (dict): The attributes of the action link.

            Returns:
                function: The view function.
            """

            def action_link_view(request, pk):
                """
                Handles the action link view.

                Args:
                    request (HttpRequest): The HTTP request object.
                    pk (int): The primary key of the object.

                Returns:
                    HttpResponse: The HTTP response.
                """
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

    class Media:
        """
        Media class to include JavaScript files.
        """
        js = ['django_reusable/js/enhanced-admin-mixin.js']


class ReadonlyAdmin(admin.ModelAdmin):
    """
    A Django admin class that makes the model read-only by disabling add and delete permissions,
    and making all fields read-only.

    Args:
        model (Model): The model class being registered with the admin.
        admin_site (AdminSite): The admin site instance.
    """

    def has_delete_permission(self, request, obj=None):
        """
        Disables delete permission for all objects.

        Args:
            request (HttpRequest): The HTTP request object.
            obj (Model, optional): The model instance. Defaults to None.

        Returns:
            bool: Always returns False to disable delete permission.
        """
        return False

    def has_add_permission(self, request):
        """
        Disables add permission.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            bool: Always returns False to disable add permission.
        """
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        Makes all fields read-only.

        Args:
            request (HttpRequest): The HTTP request object.
            obj (Model, optional): The model instance. Defaults to None.

        Returns:
            list: A list of field names to be read-only.
        """
        return self.get_list_display(request)

    def __init__(self, model, admin_site):
        """
        Initializes the ReadonlyAdmin class.

        Args:
            model (Model): The model class being registered with the admin.
            admin_site (AdminSite): The admin site instance.
        """
        self.list_display = [field.name for field in model._meta.fields if field.name
                             not in {'id', 'created', 'modified'}]
        super().__init__(model, admin_site)
