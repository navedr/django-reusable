from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from django_reusable.admin.mixins import EnhancedAdminMixin
from django_reusable.logging.loggers import PrintLogger
from .models import Person, Album, Musician


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

    list_display = fields = ['first_name', 'last_name', 'position', 'alert_name', 'say_hello', 'throw_error',
                             'person_manager', 'person_table']


class MusicianAdmin(admin.ModelAdmin):
    pass


class AlbumAdmin(admin.ModelAdmin):
    pass


admin.site.register(Person, PersonAdmin)
admin.site.register(Musician, MusicianAdmin)
admin.site.register(Album, AlbumAdmin)
