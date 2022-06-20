from collections import OrderedDict

from django import forms
from django.conf.urls import url
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, include
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, UpdateView, DeleteView
from django_tables2 import SingleTableView, LinkColumn, A

from django_reusable.django_tables2.table_mixins import EnhancedTable
from django_reusable.user_utils import current_user_has_perms


class CRUDViews(UserPassesTestMixin, SingleTableView):
    template_name = 'django_reusable/crud/index.pug'
    model = None
    title = None
    table_exclude = []
    table_fields = None
    extra_table_columns = []
    allow_table_ordering = True
    name = 'crud-view'
    edit_fields = []
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

    @classmethod
    def get_edit_url_name(cls):
        return f'{cls.name}_-_edit'

    @classmethod
    def get_delete_url_name(cls):
        return f'{cls.name}_-_delete'

    @classmethod
    def get_add_url_name(cls):
        return f'{cls.name}_-_add'

    @classmethod
    def get_list_url_name(cls):
        return f'{cls.name}'

    @classmethod
    def has_perms(cls):
        return current_user_has_perms(cls.perms) if cls.perms else True

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        list_view_instance = cls(**initkwargs)

        class ViewCommon(UserPassesTestMixin):
            success_url = reverse_lazy(cls.get_list_url_name())
            model = cls.model
            raise_exception = True

            def test_func(self):
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
            fields = cls.edit_fields

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
            def form_valid(self, form):
                response = super().form_valid(form)
                messages.info(self.request, f"New {cls.object_title} '{self.object}' created successfully!")
                return response

        class CRUDUpdateView(EditViewCommon, UpdateView):
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

        if cls.name == 'crud-view' or not cls.name:
            raise ImproperlyConfigured("{name} property needs to be set")

        if not cls.base_template:
            raise ImproperlyConfigured("{base_template} property needs to be set")

        add_urls = []
        if cls.add_wizard_view_class:
            add_urls.extend(cls._get_add_wizard_urls())
        else:
            add_urls.append(url(r'^new/$', CRUDCreateView.as_view(), name=cls.get_add_url_name()))

        url_patterns = [
            url(r'^$', view, name=cls.get_list_url_name()),
            *add_urls,
            url(r'^(?P<pk>\d+)/edit/$', CRUDUpdateView.as_view(), name=cls.get_edit_url_name()),
            url(r'^(?P<pk>\d+)/delete/$', CRUDDeleteView.as_view(), name=cls.get_delete_url_name())
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

            def get_context_data(self, form, **kwargs):
                context_data = super().get_context_data(form, **kwargs)
                if self.steps.current == 'review':
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
                    context_data['all_data'] = OrderedDict(
                        (all_field_labels.get(k, k), v) for (k, v) in all_data.items())
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
            url(r'^new/(?P<step>.+)/$', add_wizard_view, name=step_url_name),
            url(r'^new/$', add_wizard_view, name=add_url_name),
        ]

    def test_func(self):
        return self.has_perms()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs) or {}
        context_data.update(
            title=self.title,
            add_url=self.get_add_url_name(),
            object_title=self.object_title,
            allow_add=self.get_allow_add(),
            base_template=self.base_template,
            additional_index_links=self.get_additional_index_links()
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
        return LinkColumn(viewname=self.get_edit_url_name(),
                          text=mark_safe('<i class="fa fa-edit"></i>'),
                          args=[A('pk')],
                          verbose_name='',
                          attrs={'a': {'class': 'btn btn-sm btn-primary'}})

    def _get_delete_link_column(self):
        crud = self

        class DeleteLinkColumn(LinkColumn):
            def render(self, value, record, bound_column):
                if crud.allow_delete_for_record(record):
                    return super().render(value, record, bound_column)
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
        return self.get_allow_delete()

    def allow_edit_for_record(self, record):
        return self.get_allow_edit()

    def get_allow_add(self):
        return self.allow_add

    def get_table_exclude(self):
        return self.table_exclude

    def get_extra_table_columns(self):
        return self.extra_table_columns

    def get_table_fields(self):
        return self.table_fields

    def get_edit_fields(self):
        return self.edit_fields

    def get_table_class(self):
        class CRUDViewTable(EnhancedTable):
            class Meta:
                model = self.model
                orderable = self.allow_table_ordering

        return CRUDViewTable

    def get_edit_view_tables(self, record):
        return []

    def get_additional_index_links(self):
        return self.additional_index_links
