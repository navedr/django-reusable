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
    """Enhanced inline mixin with select2 support and queryset customization.

    Provides auto-updating templates, Select2 widget integration for inline
    fields, and fine-grained control over field querysets.

    Attributes:
        auto_update_template: If True, uses the enhanced admin inline template
            that supports dynamic JS updates. Defaults to True.
        select2_inlines_fields: List of field names to render with Select2 widgets.
        default_field_queryset: Dict mapping field names to default querysets,
            e.g. ``{'city': City.objects.filter(active=True)}``.
        limit_field_queryset_model_fields: Dict mapping inline field names to
            parent model fields used to filter the inline queryset,
            e.g. ``{'city': 'country'}``.
        limit_saved_queryset_value_fields: List of field names whose querysets
            should be limited to the currently saved value for existing rows.

    Example:
        ```python
        class MusicianConcertInline(EnhancedAdminInlineMixin, admin.TabularInline):
            model = MusicianConcert
            extra = 0
            select2_inlines_fields = ['city']
        ```
    """
    auto_update_template = True
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
            field.widget.attrs['class'] = 'inline-select2' if not self.auto_update_template else 'dr-inline-select2'
        return field

    @property
    def media(self):
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
    """Base admin mixin that restricts delete permissions to object owners.

    When ``only_delete_owned`` is True, only the user referenced by
    ``user_field`` on the model instance (or users with the ``user.is_admin``
    permission) can delete that object.

    Attributes:
        user_field: Name of the ForeignKey field on the model that points to
            the owning user. Defaults to ``'created_by'``.
        only_delete_owned: If True, non-admin users can only delete objects
            they own. Defaults to False.
    """
    user_field = 'created_by'
    only_delete_owned = False

    def has_delete_permission(self, request, obj=None):
        if self.only_delete_owned and not request.user.has_perm('user.is_admin'):
            if not (obj and getattr(obj, self.user_field).id == request.user.id):
                return False
        return super().has_delete_permission(request, obj)


class AjaxActionMixin:
    """Mixin that adds AJAX-powered action buttons to admin list rows.

    Each entry in ``ajax_action_fields`` renders as a button in the changelist
    that triggers a server-side callback via AJAX without a full page reload.

    Attributes:
        ajax_action_fields: List of ``(field_name, config)`` tuples where
            ``config`` is a dict with keys:

            - ``btn_text`` (str): Button label.
            - ``btn_class`` (str): CSS classes. Defaults to ``'btn btn-warning'``.
            - ``additional_html`` (str): Extra HTML appended after the button.
            - ``callback`` (callable): ``fn(admin, request, pk)`` invoked on click.
            - ``short_desc`` (str): Column header text.
            - ``confirm`` (str): Confirmation prompt shown before the action.

    Example:
        ```python
        ajax_action_fields = [
            ('test_ajax', dict(
                btn_text='Test Ajax',
                additional_html='<b>hi</b>',
                callback=lambda admin, request, pk: f"done {pk}!",
                confirm='Are you sure?',
            )),
        ]
        ```
    """
    ajax_action_fields = []

    def get_ajax_action_fields(self):
        return self.ajax_action_fields

    def get_callback_key(self, name):
        return f'{self.__class__.__name__}_{name}'

    def ajax_action_callback(self, request, name, object_id=None):
        match = find(lambda x: x[0] == name, self.get_ajax_action_fields())
        if match:
            config = match[1]
            callback = config.get('callback')
            if callback:
                result = callback(self, request, object_id)
                return HttpResponse(result)
        return HttpResponse(f'no callback params defined for {name}')

    def _create_ajax_actions_fn(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        for name, config in self.get_ajax_action_fields():
            btn_text = config.get('btn_text', 'Button')
            btn_class = config.get('btn_class', 'btn btn-warning')
            confirm = config.get('confirm', "")

            @mark_safe
            def func(instance):
                url = reverse('admin:%s_%s-dr-ajax-action' % info, args=(name, instance.id))
                return (f'<button data-confirm="{confirm}" class="{btn_class} dr-ajax-action-btn" data-url="{url}">'
                        f'{btn_text}</button>' +
                        config.get('additional_html', ''))

            func.short_description = config.get('short_desc', btn_text)
            func.__name__ = name
            setattr(self, func.__name__, func)


class ExtraChangelistLinksMixin:
    """Mixin that adds extra link buttons to the admin changelist view.

    Attributes:
        extra_changelist_links: List of ``(url, config)`` tuples where
            ``config`` is a dict with keys:

            - ``link_text`` (str): Link label. Defaults to ``'Link'``.
            - ``link_class`` (str): CSS classes. Defaults to ``'btn-link'``.
            - ``new_tab`` (bool): Open in a new tab. Defaults to False.
            - ``user_passes_test`` (callable): ``fn(user) -> bool`` to
              conditionally show the link. Defaults to always visible.

    Example:
        ```python
        extra_changelist_links = [
            (reverse_lazy('person_manager'), dict(
                link_text='Manager',
                link_class='btn btn-warning',
                new_tab=True,
            )),
        ]
        ```
    """
    extra_changelist_links = []

    def _get_applicable_extra_changelist_links(self, request):
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
        return self.extra_changelist_links

    def _changelist_mixin_js_data(self, request):
        return dict(
            extra_links=[dict(url=url, config=config) for (url, config) in
                         self._get_applicable_extra_changelist_links(request)]
        )


class ExtraChangeFormButtonsMixin:
    """Mixin that adds extra submit buttons to the admin change form.

    Buttons appear alongside the default save buttons and trigger custom
    callbacks on form submission.

    Attributes:
        extra_change_form_buttons: List of ``(name, config)`` tuples where
            ``config`` is a dict with keys:

            - ``btn_text`` (str): Button label. Defaults to ``'Button'``.
            - ``btn_class`` (str): CSS classes. Defaults to ``'btn-primary'``.
            - ``stay_on_page`` (bool): Redirect back to the same change form
              after the callback. Defaults to False.
            - ``custom_redirect`` (bool): If True, the callback's return value
              is used as the HTTP response. Defaults to False.
            - ``confirm`` (str): Confirmation prompt before submission.
            - ``callback`` (callable): ``fn(admin, request, pk)`` invoked when
              the button is clicked. Return a message string or an
              ``HttpResponse`` (when ``custom_redirect=True``).
            - ``user_passes_test`` (callable): ``fn(user) -> bool``.
            - ``pk_passes_test`` (callable): ``fn(pk) -> bool``.

    Example:
        ```python
        extra_change_form_buttons = [
            ('test', dict(
                btn_text='Test',
                btn_class='btn-warning',
                stay_on_page=True,
                callback=lambda admin, request, pk: print("clicked", pk),
            )),
        ]
        ```
    """
    extra_change_form_buttons = []

    def _get_applicable_extra_change_form_buttons(self, request, pk):
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
        extra_context.update(
            extra_submit_buttons=[
                (f'__{name}', config['btn_class'], config['btn_text'])
                for (name, config) in self._get_applicable_extra_change_form_buttons(request, pk)
            ]
        )

    def _handle_extra_change_form_buttons(self, request, object_id):
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
        return dict(
            object_id=object_id,
            extra_submit_buttons=[
                dict(name=name, config=config)
                for (name, config) in self._get_applicable_extra_change_form_buttons(request, object_id)
            ]
        )


class CustomFieldsMixin:
    """Mixin that adds computed read-only fields to the admin.

    Each entry becomes a callable on the admin class and is automatically
    added to ``readonly_fields``.

    Attributes:
        custom_fields: List of tuples in the format
            ``(field_name, callable, short_desc)`` where:

            - ``field_name`` (str): Name used as the attribute and column key.
            - ``callable``: ``fn(instance)`` returning the display value.
            - ``short_desc`` (str, optional): Column header text.

    Example:
        ```python
        custom_fields = [
            ('nom', lambda instance: instance.first_name, 'Nickname'),
        ]
        ```
    """
    custom_fields = []

    def _create_custom_fields_fn(self):
        for f in self.custom_fields:
            func = f[1]
            func.allow_tags = True
            if len(f) > 2:
                func.short_description = f[2]
            func.__name__ = f[0]
            setattr(self, func.__name__, func)


class ActionLinksMixin:
    """Mixin that adds clickable action link buttons per row in the changelist.

    Each action link renders as a button that navigates to a custom URL
    endpoint, executes a callback with the model instance, and redirects back.

    Attributes:
        action_links: List of ``(name, config)`` tuples where ``config`` is
            a dict with keys:

            - ``btn_text`` (str): Button label.
            - ``btn_class`` (str): CSS classes for the ``<a>`` tag.
            - ``callback`` (callable): ``fn(instance)`` called when clicked.
              Required -- entries without ``callback`` are skipped.
            - ``short_desc`` (str): Column header text.
            - ``custom_redirect`` (bool): If True, the callback's return value
              is used as the HTTP response instead of redirecting back.

    Example:
        ```python
        action_links = [
            ('alert_name', dict(
                btn_text='Alert Name',
                btn_class='btn-info',
                callback=lambda instance: logger.info(instance),
            )),
            ('go_to_page', dict(
                btn_text='View',
                btn_class='btn-primary',
                custom_redirect=True,
                callback=lambda instance: redirect(instance.get_absolute_url()),
            )),
        ]
        ```
    """
    action_links = []

    def _create_action_links_fn(self):
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


class EnhancedAdminMixin(admin.ModelAdmin,
                         EnhancedBaseAdminMixin,
                         ExtraChangelistLinksMixin,
                         ExtraChangeFormButtonsMixin,
                         AjaxActionMixin,
                         CustomFieldsMixin,
                         ActionLinksMixin):
    """Main enhanced admin mixin combining all django-reusable admin features.

    Combines ``EnhancedBaseAdminMixin``, ``ExtraChangelistLinksMixin``,
    ``ExtraChangeFormButtonsMixin``, ``AjaxActionMixin``, ``CustomFieldsMixin``,
    and ``ActionLinksMixin`` into a single drop-in replacement for
    ``admin.ModelAdmin``.

    Attributes:
        auto_update_template: If True, uses enhanced JS-driven templates that
            inject extra links, buttons, and AJAX actions dynamically.
            Defaults to True.
        default_filters: List of default query-string filter expressions
            applied when navigating to the changelist without explicit filters,
            e.g. ``['status=active', 'archived=false']``.
        search_in_choices: List of ``(field_lookup, label)`` tuples that
            populate a "Search In" dropdown filter, allowing users to search
            within a specific field,
            e.g. ``[('first_name__icontains', 'First Name')]``.
        search_in_required: If True, a search query without a "Search In"
            selection shows a warning and returns no results. Defaults to False.
        lazy_load_fields: List of readonly field names whose content should be
            fetched asynchronously after page load. The field method should
            return a placeholder (e.g. "Loading..."), and a corresponding
            ``get_<field_name>_content(self, obj)`` method provides the real
            content via an AJAX endpoint. Requires ``auto_update_template=True``.

    Example:
        ```python
        class PersonAdmin(EnhancedAdminMixin):
            action_links = [
                ('alert_name', dict(btn_text='Alert', btn_class='btn-info',
                                    callback=lambda inst: logger.info(inst))),
            ]
            extra_changelist_links = [
                (reverse_lazy('person_manager'), dict(
                    link_text='Manager', link_class='btn btn-warning', new_tab=True)),
            ]
            ajax_action_fields = [
                ('test_ajax', dict(btn_text='Test', callback=lambda a, r, pk: "done")),
            ]
            custom_fields = [
                ('nom', lambda instance: instance.first_name),
            ]
            lazy_load_fields = ['expensive_field']

            def expensive_field(self, instance):
                return 'Loading...'

            def get_expensive_field_content(self, instance):
                return instance.compute_something_slow()
        ```
    """
    auto_update_template = True
    default_filters = []
    search_in_choices = []
    search_in_required = False

    def _apply_search_in_choices(self):
        if self.search_in_choices:
            if not ifilter(lambda x: 'SearchInFilter' in str(x), self.list_filter):
                filter_class = type('%sSearchInFilter' % self.__class__.__name__, (SearchInFilter,),
                                    {'lookup_choices': sorted(self.search_in_choices, key=lambda x: x[1])})
                self.list_filter.insert(0, filter_class)
            self.base_search_fields = map(lambda xy: xy[0], self.search_in_choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_search_in_choices()
        self._create_custom_fields_fn()
        self._create_action_links_fn()
        self._create_ajax_actions_fn()

    def get_search_fields(self, request):
        search_fields = deepcopy(self.search_fields)
        if self.search_in_choices:
            search_in_value = request.GET.get(SearchInFilter.parameter_name)
            if search_in_value:
                search_fields = [search_in_value]
            elif self.search_in_required and request.GET.get('q', '').strip():
                messages.warning(request, 'Please select a "Search In" option to search.')
                search_fields = []
            else:
                search_fields = search_fields or self.base_search_fields
        return search_fields

    def hide_save_buttons(self, request, object_id):
        """Hook to conditionally hide save buttons and block POST requests.

        Override this to disable editing for specific objects or users.

        Args:
            request: The current ``HttpRequest``.
            object_id: Primary key of the object being edited.

        Returns:
            True to hide save buttons and reject POST, False otherwise.
        """
        return False

    def get_changelist_extra_context(self, request):
        """Hook to add extra template context to the changelist view.

        Args:
            request: The current ``HttpRequest``.

        Returns:
            Dict of extra context variables merged into the changelist template.
        """
        return {}

    def custom_changelist_actions(self, request):
        """Hook called at the start of ``changelist_view`` for side effects.

        Use this to perform actions (e.g. bulk updates) before the changelist
        is rendered.

        Args:
            request: The current ``HttpRequest``.
        """
        pass

    def _get_default_filters_redirect(self, request):
        if self.default_filters:
            try:
                test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])
                if test and test[-1] and not test[-1].startswith('?') and not request.META['QUERY_STRING']:
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
                [x[0] for x in self.action_links] +
                [x[0] for x in self.get_ajax_action_fields()])

    def get_fieldset_section_exclusions(self, request, obj):
        """Hook to dynamically exclude entire fieldset sections by title.

        Args:
            request: The current ``HttpRequest``.
            obj: The model instance being edited, or None for add views.

        Returns:
            List of fieldset title strings to exclude.
        """
        return []

    def get_fieldset_field_exclusions(self, request, obj):
        """Hook to dynamically exclude individual fields from all fieldsets.

        Args:
            request: The current ``HttpRequest``.
            obj: The model instance being edited, or None for add views.

        Returns:
            List of field name strings to remove from fieldsets.
        """
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

    lazy_load_fields = []

    def _get_lazy_field_content(self, request, object_id, field_name):
        method = getattr(self, f'get_{field_name}_content', None)
        if method:
            obj = self.model.objects.get(pk=object_id)
            return HttpResponse(method(obj))
        return HttpResponse('')

    def _get_common_mixin_js_data(self):
        return dict(
            app=self.model._meta.app_label,
            model=self.model._meta.model_name,
            enabled=self.auto_update_template
        )

    def _changelist_mixin_js_data(self, request):
        return JsonResponse(dict(
            **self._get_common_mixin_js_data(),
            **super()._changelist_mixin_js_data(request)
        ), encoder=CustomEncoder)

    def _change_form_mixin_js_data(self, request, object_id=None):
        return JsonResponse(dict(
            **self._get_common_mixin_js_data(),
            hide_save_buttons=self.hide_save_buttons(request, object_id),
            lazy_load_fields=self.lazy_load_fields if object_id else [],
            **super()._change_form_mixin_js_data(request, object_id)
        ), encoder=CustomEncoder)

    def get_urls(self):
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
            path('<path:object_id>/change/dr-lazy-field/<str:field_name>/',
                 self._get_lazy_field_content,
                 name='%s_%s-dr-lazy-field' % info),
        ]

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

    class Media:
        js = ['django_reusable/js/enhanced-admin-mixin.js']


class ReadonlyAdmin(admin.ModelAdmin):
    """Read-only admin view that disables add, delete, and editing.

    All model fields (except ``id``, ``created``, ``modified``) are displayed
    as read-only in both the list and change views. Useful for audit/log
    tables that should be viewable but not modifiable.
    """

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return self.get_list_display(request)

    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name
                             not in {'id', 'created', 'modified'}]
        super().__init__(model, admin_site)
