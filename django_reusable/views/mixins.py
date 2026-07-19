from collections import OrderedDict
from functools import reduce

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction, models
from django.db.models import QuerySet, Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, include, re_path
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DeleteView
from django_tables2 import SingleTableView, LinkColumn, A

from django_reusable.django_tables2.table_mixins import EnhancedTable
from django_reusable.utils import find
from django_reusable.utils.user_utils import current_user_has_perms


class CRUDViews(UserPassesTestMixin, SingleTableView):
    """Full CRUD view generator that produces list, create, update, and delete views.

    Subclass this and call ``as_view()`` to get a set of URL patterns providing
    a complete CRUD interface backed by ``django-tables2`` for listing and
    Django generic views for create/update/delete.

    Attributes:
        model: The Django model class for this CRUD set.
        name: Unique URL namespace prefix. Must be overridden from the default
            ``'crud-view'``.
        title: Page title displayed in the list view header.
        table_fields: List of field names to show in the table. If None, all
            fields are shown (minus ``table_exclude``).
        table_exclude: List of field names to hide from the table.
        extra_table_columns: List of extra ``django-tables2`` column tuples
            ``(name, Column)`` appended to the table.
        allow_table_ordering: Enable column-header sorting. Defaults to True.
        edit_fields: List of field names shown on the edit form.
        add_fields: List of field names shown on the add form. Falls back to
            ``edit_fields`` if empty.
        allow_edit: Global toggle for edit links. Defaults to True.
        allow_delete: Global toggle for delete links. Defaults to True.
        allow_add: Global toggle for the "Add" button. Defaults to True.
        edit_form_class: Optional custom ``ModelForm`` class for edit/add views.
        object_title: Human-readable singular name for the model
            (e.g. ``'Person'``), used in flash messages.
        perms: List of permission strings required to access these views.
        base_template: Template that the CRUD templates extend. **Required**.
        raise_exception: If True, raise ``PermissionDenied`` instead of
            redirecting to login. Defaults to True.
        additional_index_links: List of extra links shown on the index page.
        add_wizard_view_class: Optional ``SessionWizardView`` subclass used
            instead of the default single-step create form.
        filters: List of filter definitions. Each entry is either a field name
            string (auto-detected choices) or a ``(field, config)`` tuple where
            config has keys ``label``, ``get_choices`` (callable returning
            choice tuples), and optionally ``filter`` (callable
            ``fn(qs, value) -> qs``).
        filters_widget: Form widget for filter dropdowns.
        show_filter_label: Show labels next to filter fields. Defaults to False.
        search_fields: List of field lookups for the search box (e.g.
            ``['first_name', 'last_name']``). Empty list disables search.

    Example:
        ```python
        class ManagerPersonView(CRUDViews):
            base_template = 'admin/base_site.html'
            name = 'person_manager'
            model = Person
            table_fields = ['first_name', 'last_name', 'position']
            edit_fields = ['first_name', 'last_name']
            object_title = 'Person'
            filters = [
                'position',
                ('gender', dict(
                    label='Gender',
                    get_choices=lambda: [('Male', 'Male'), ('Female', 'Female')],
                    filter=lambda qs, val: qs.filter(first_name='Naved') if val == 'Male' else qs,
                )),
            ]
            search_fields = ['first_name', 'last_name']

        urlpatterns = [
            re_path(r'^people/', ManagerPersonView.as_view()),
        ]
        ```
    """
    template_name = 'django_reusable/crud/index.pug'
    model = None
    title = None
    table_exclude = []
    table_fields = None
    extra_table_columns = []
    allow_table_ordering = True
    name = 'crud-view'
    edit_fields = []
    add_fields = []
    allow_edit = True
    allow_delete = True
    allow_add = True
    edit_form_class = None
    object_title = ''
    perms = []
    base_template = None
    raise_exception = True
    additional_index_links = []
    add_wizard_view_class = None
    filters = []
    filters_widget = forms.Select(attrs={'class': 'form-control'})
    show_filter_label = False
    search_fields = []

    @classmethod
    def get_edit_url_name(cls):
        """Return the URL name for the edit view.

        Returns:
            URL name string in the format ``'{name}_-_edit'``.
        """
        return f'{cls.name}_-_edit'

    @classmethod
    def get_delete_url_name(cls):
        """Return the URL name for the delete view.

        Returns:
            URL name string in the format ``'{name}_-_delete'``.
        """
        return f'{cls.name}_-_delete'

    @classmethod
    def get_add_url_name(cls):
        """Return the URL name for the add/create view.

        Returns:
            URL name string in the format ``'{name}_-_add'``.
        """
        return f'{cls.name}_-_add'

    @classmethod
    def get_list_url_name(cls):
        """Return the URL name for the list/index view.

        Returns:
            URL name string equal to ``name``.
        """
        return f'{cls.name}'

    @classmethod
    def has_perms(cls):
        """Check if the current user has the required permissions.

        Returns:
            True if ``perms`` is empty or the current user has all listed
            permissions.
        """
        return current_user_has_perms(cls.perms) if cls.perms else True

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        list_view_instance = cls(**initkwargs)

        class ViewCommon(UserPassesTestMixin):
            model = cls.model
            raise_exception = True

            def test_func(self):
                list_view_instance.request = self.request
                return cls.has_perms()

            def get_context_data(self, **kwargs):
                context_data = super().get_context_data(**kwargs) or {}
                context_data.update(
                    title=cls.title,
                    index_url=cls.get_list_url_name(),
                    object_title=cls.object_title,
                    base_template=cls.base_template
                )
                return context_data

        class EditViewCommon(ViewCommon):
            template_name = 'django_reusable/crud/create_or_update.pug'

            def get_form_class(self):
                if cls.edit_form_class:
                    return cls.edit_form_class
                return super().get_form_class()

            def get_context_data(self, **kwargs):
                context_data = super().get_context_data(**kwargs) or {}
                context_data.update(
                    additional_tables=list_view_instance.get_edit_view_tables(self.object)
                )
                return context_data

        class CRUDCreateView(EditViewCommon, CreateView):
            fields = cls.add_fields or cls.edit_fields

            def form_valid(self, form):
                response = super().form_valid(form)
                messages.info(self.request, f"New {cls.object_title} '{self.object}' created successfully!")
                return response

            def get_success_url(self):
                return list_view_instance.get_success_url("create", self.object.pk)

        class CRUDUpdateView(EditViewCommon, UpdateView):
            fields = cls.edit_fields

            def form_valid(self, form):
                response = super().form_valid(form)
                messages.info(self.request, f"{cls.object_title} '{self.object}' has been updated!")
                return response

            def test_func(self):
                has_perm = super().test_func()
                if has_perm:
                    return list_view_instance.get_queryset().filter(id=self.kwargs['pk']).exists()
                return has_perm

            def get_context_data(self, **kwargs):
                context_data = super().get_context_data(**kwargs) or {}
                record = list_view_instance.get_queryset().filter(id=self.kwargs['pk']).first()
                context_data.update(
                    disable_submit=not list_view_instance.allow_edit_for_record(record)
                )
                return context_data

            def post(self, request, *args, **kwargs):
                obj = self.get_object()
                can_edit = list_view_instance.allow_edit_for_record(obj)
                if not can_edit:
                    messages.error(request, f'You cannot edit {obj}')
                    return super().get(request, *args, **kwargs)
                return super().post(request, *args, **kwargs)

            def get_success_url(self):
                return list_view_instance.get_success_url("update", self.object.pk)

        class CRUDDeleteView(ViewCommon, DeleteView):
            template_name = 'django_reusable/crud/delete.pug'

            def test_func(self):
                has_perm = super().test_func()
                if has_perm:
                    record = list_view_instance.get_queryset().filter(id=self.kwargs['pk']).first()
                    return record and list_view_instance.allow_delete_for_record(record)
                return has_perm

            def delete(self, request, *args, **kwargs):
                response = super().delete(request, *args, **kwargs)
                messages.info(self.request, f"{cls.object_title} '{self.object}' has been deleted!")
                return response

            def get_success_url(self):
                return list_view_instance.get_success_url("delete", self.object.pk)

        if cls.name == 'crud-view' or not cls.name:
            raise ImproperlyConfigured("{name} property needs to be set")

        if not cls.base_template:
            raise ImproperlyConfigured("{base_template} property needs to be set")

        add_urls = []
        if cls.add_wizard_view_class:
            add_urls.extend(cls._get_add_wizard_urls())
        else:
            add_urls.append(re_path(r'^new/$', CRUDCreateView.as_view(), name=cls.get_add_url_name()))

        url_patterns = [
            re_path(r'^$', view, name=cls.get_list_url_name()),
            *add_urls,
            re_path(r'^(?P<pk>\d+)/edit/$', CRUDUpdateView.as_view(), name=cls.get_edit_url_name()),
            re_path(r'^(?P<pk>\d+)/delete/$', CRUDDeleteView.as_view(), name=cls.get_delete_url_name())
        ]
        return include(url_patterns)

    @classmethod
    def _get_add_wizard_urls(cls):
        add_url_name = cls.get_add_url_name()
        step_url_name = f'{add_url_name}_step'

        class ReviewForm(forms.Form):
            page_title = 'Review'
            confirm = forms.BooleanField(label='All details correct?')

        class AddWizardView(cls.add_wizard_view_class):
            template_name = 'django_reusable/crud/add_wizard.pug'
            form_list = cls.add_wizard_view_class.form_list + [('review', ReviewForm)]

            def _add_review_data(self, context_data):
                all_data = self.get_all_cleaned_data()
                all_field_labels = {}
                for form_key in self.get_form_list():
                    form_obj = self.get_form(
                        step=form_key,
                        data=self.storage.get_step_data(form_key),
                        files=self.storage.get_step_files(form_key)
                    )
                    if hasattr(form_obj, 'fields'):
                        for field in form_obj.fields.keys():
                            all_field_labels[field] = form_obj.fields[field].label or field.replace(
                                '_', ' ').title()
                for k, v in all_data.items():
                    if isinstance(v, QuerySet):
                        all_data[k] = mark_safe('<ul>' + ''.join([f'<li>{x}</li>' for x in v]) + '</ul>')
                context_data['all_data'] = OrderedDict(
                    (all_field_labels.get(k, k), v) for (k, v) in all_data.items())

            def get_context_data(self, form, **kwargs):
                context_data = super().get_context_data(form, **kwargs)
                if self.steps.current == 'review':
                    self._add_review_data(context_data)
                current_form_index = list(self.get_form_list().keys()).index(self.steps.current)
                context_data.update(
                    step_url_name=step_url_name,
                    object_title=cls.object_title,
                    list_url_name=cls.get_list_url_name(),
                    base_template=cls.base_template,
                    complete_percent=int(round(current_form_index * 100 / len(list(self.get_form_list().keys())), 0))
                )
                return context_data

            @transaction.atomic
            def done(self, form_list, **kwargs):
                super().done(form_list, **kwargs)
                messages.info(self.request, f'New {cls.object_title} created successfully!')
                return HttpResponseRedirect(reverse_lazy(cls.get_list_url_name()))

        add_wizard_view = AddWizardView.as_view(url_name=step_url_name,
                                                done_step_name='finished')
        return [
            re_path(r'^new/(?P<step>.+)/$', add_wizard_view, name=step_url_name),
            re_path(r'^new/$', add_wizard_view, name=add_url_name),
        ]

    def test_func(self):
        return self.has_perms()

    def _get_filters_form(self):
        list_view = self

        class FilterForm(forms.Form):
            q = forms.CharField(required=False, label='',
                                widget=forms.TextInput(attrs={'placeholder': 'Search', 'class': 'form-control'}))

            def _get_filter_choices_for_model_field(self, field, model_field):
                if isinstance(model_field, (models.ForeignKey, models.ManyToManyField)):
                    return [(x.pk, str(x)) for x in model_field.related_model.objects.all()]
                elif getattr(model_field, 'choices', []):
                    return model_field.choices
                else:
                    distinct_values = list_view.model.objects.order_by(field).values_list(field, flat=True).distinct()
                    return [(x, x) for x in distinct_values]

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                common_attrs = dict(required=False, widget=list_view.filters_widget)
                if not list_view.show_filter_label:
                    common_attrs['label'] = ''
                for _field in list_view.get_filters():
                    if isinstance(_field, tuple):
                        field, opts = _field
                        self.fields[field] = forms.ChoiceField(choices=[('', opts.get('label', field.title()))]
                                                                       + opts['get_choices'](),
                                                               **common_attrs)
                    elif isinstance(_field, str):
                        model_field = find(lambda f: f.name == _field, list_view.model._meta.fields)
                        self.fields[_field] = forms.ChoiceField(choices=[('', model_field.verbose_name.title())] +
                                                                        self._get_filter_choices_for_model_field(
                                                                            _field, model_field),
                                                                **common_attrs)

                if not list_view.get_search_fields():
                    del self.fields['q']

            class Meta:
                fields = (['q'] if self.get_search_fields() else []) + [x for x in self.get_filters() if
                                                                        isinstance(x, str)]

        return FilterForm(self.request.GET)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs) or {}
        filters_form = self._get_filters_form()
        show_clear_filter = filters_form.is_valid() and any([x for x in filters_form.cleaned_data.values() if x])
        context_data.update(
            title=self.title,
            add_url=self.get_add_url_name(),
            object_title=self.object_title,
            allow_add=self.get_allow_add(),
            base_template=self.base_template,
            additional_index_links=self.get_additional_index_links(),
            filters_form=filters_form,
            show_clear_filter=show_clear_filter,
            show_search_button=self.get_filters() or self.get_search_fields()
        )
        return context_data

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs() or {}
        extra_columns = self.get_extra_table_columns()
        extra_columns.append(('edit', self._get_edit_link_column()))
        if self.get_allow_delete():
            extra_columns.append(('delete', self._get_delete_link_column()))
        kwargs.update(
            exclude=self.get_table_exclude(),
            fields=self.get_table_fields(),
            attrs={'class': 'table table-bordered'},
            extra_columns=extra_columns
        )
        return kwargs

    def _get_edit_link_column(self):
        crud_instance = self
        class EditColumn(LinkColumn):
            def text_value(self, record, value):
                if not crud_instance.allow_edit_for_record(record):
                    return mark_safe('<i class="fa fa-eye"></i>')
                return mark_safe('<i class="fa fa-edit"></i>')

        return EditColumn(viewname=self.get_edit_url_name(),
                          text=mark_safe('<i class="fa fa-edit"></i>'),
                          args=[A('pk')],
                          verbose_name='',
                          attrs={'a': {'class': 'btn btn-sm btn-primary'}})

    def _get_delete_link_column(self):
        crud = self

        class DeleteLinkColumn(LinkColumn):
            def render(self, value, record, bound_column):
                if crud.allow_delete_for_record(record):
                    return super().render(record=record, value=value)
                return ''

        return DeleteLinkColumn(viewname=self.get_delete_url_name(),
                                text=mark_safe('<i class="fa fa-trash-alt"></i>'),
                                args=[A('pk')],
                                verbose_name='',
                                attrs={'a': {'class': 'btn btn-sm btn-danger'}})

    def get_allow_edit(self):
        return self.allow_edit

    def get_allow_delete(self):
        return self.allow_delete

    def allow_delete_for_record(self, record):
        """Hook to conditionally disable delete for a specific record.

        Args:
            record: The model instance.

        Returns:
            True if the record can be deleted.
        """
        return self.get_allow_delete()

    def allow_edit_for_record(self, record):
        """Hook to conditionally disable editing for a specific record.

        Args:
            record: The model instance.

        Returns:
            True if the record can be edited.
        """
        return self.get_allow_edit()

    def get_allow_add(self):
        return self.allow_add

    def get_table_exclude(self):
        return self.table_exclude

    def get_extra_table_columns(self):
        """Return extra columns to append to the table.

        Returns:
            List of ``(name, Column)`` tuples for ``django-tables2``.
        """
        return self.extra_table_columns

    def get_table_fields(self):
        return self.table_fields

    def get_table_class(self):
        class CRUDViewTable(EnhancedTable):
            class Meta:
                model = self.model
                orderable = self.allow_table_ordering

        return CRUDViewTable

    def get_edit_view_tables(self, record):
        """Hook to add extra tables below the edit form.

        Args:
            record: The model instance being edited.

        Returns:
            List of ``django-tables2`` table instances to render.
        """
        return []

    def get_additional_index_links(self):
        """Return extra links to display on the list/index page.

        Returns:
            List of additional link definitions.
        """
        return self.additional_index_links

    def _apply_filters(self, qs):
        filters = self.get_filters()
        search_fields = self.get_search_fields()
        if filters:
            filters_form = self._get_filters_form()
            if filters_form.is_valid():
                filtered_values = {k: v for k, v in filters_form.cleaned_data.items() if
                                   v != '' and k in filters and k != 'q'}
                qs = qs.filter(**filtered_values)
                for field, opts in [x for x in filters if isinstance(x, tuple)]:
                    if 'filter' in opts and filters_form.cleaned_data[field]:
                        qs = opts['filter'](qs, filters_form.cleaned_data[field])
                if search_fields and filters_form.cleaned_data['q']:
                    conditions = [Q(**{f'{x}__icontains': filters_form.cleaned_data['q']}) for x in search_fields]
                    qs = qs.filter(reduce(lambda x, y: x | y, conditions))
        return qs

    def get_table_data(self):
        qs = super().get_table_data()
        qs = self._apply_filters(qs)
        return qs

    def get_filters(self):
        """Return the list of filter definitions for the index view.

        Returns:
            List of field name strings or ``(field, config)`` tuples.
        """
        return self.filters

    def get_search_fields(self):
        """Return the list of field lookups used by the search box.

        Returns:
            List of field name strings for ``__icontains`` lookups.
        """
        return self.search_fields

    def get_success_url(self, type, pk):
        """Return the URL to redirect to after a successful CRUD operation.

        Override this to redirect to a detail page or stay on the edit form.

        Args:
            type: The operation type (``'create'``, ``'update'``, or ``'delete'``).
            pk: Primary key of the affected object.

        Returns:
            URL string or lazy URL.
        """
        return reverse_lazy(self.get_list_url_name())
