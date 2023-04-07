from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe

from django_reusable.admin.mixins import EnhancedAdminMixin
from django_reusable.logging.loggers import PrintLogger
from .models import Person, Album, Musician, MusicianConcert


class MusicianInline(admin.TabularInline):
    model = Musician
    extra = 0
    readonly_fields = ['edit_concerts']

    def edit_concerts(self, instance):
        return mark_safe(f'''<a href="javascript:window.open('https://www.w3schools.com', 
        'edit_caterer','height=200,width=150')">Concerts</a>''')


class PersonAdmin(EnhancedAdminMixin):
    action_links = [
        ('alert_name', dict(btn_text='Alert Name', btn_class='btn-info',
                            callback=lambda instance: PrintLogger('alert_name').info(instance))),
        ('say_hello', dict(btn_text='Say Hello', btn_class='btn-warning', callback=lambda instance: print("Hello"))),
        ('person_manager', dict(btn_text='Manager', custom_redirect=True, btn_class='btn-primary',
                                callback=lambda instance: redirect(reverse('person_manager')))),
        ('person_table', dict(btn_text='Table', custom_redirect=True, btn_class='btn-primary',
                              callback=lambda instance: redirect(reverse('person_table')))),
        ('throw_error', dict(btn_text='Throw Error', btn_class='btn-danger', callback=lambda instance: mark_safe())),
    ]
    inlines = [MusicianInline]

    list_display = fields = ['first_name', 'last_name', 'position', 'alert_name', 'say_hello', 'throw_error',
                             'person_manager', 'person_table']
    """
        List of tuples:
        ('name', dict(btn_text, btn_class, stay_on_page, callback, user_passes_test, pk_passes_test))
    """
    extra_change_form_buttons = [
        ('test', dict(btn_text='Test', btn_class='btn-warning', stay_on_page=True,
                      callback=lambda *args: print("clicked", args)))
    ]
    """
        List of tuples:
        (url, dict(link_text, link_class, new_tab, user_passes_test))
    """
    extra_changelist_links = [
        (reverse_lazy('person_manager'), dict(link_text='Manager', link_class='btn btn-warning', new_tab=True))
    ]


class MusicianConcertInline(admin.TabularInline):
    model = MusicianConcert
    extra = 0


class MusicianAdmin(admin.ModelAdmin):
    inlines = [MusicianConcertInline]


class AlbumAdmin(admin.ModelAdmin):
    pass


admin.site.register(Person, PersonAdmin)
admin.site.register(Musician, MusicianAdmin)
admin.site.register(Album, AlbumAdmin)
