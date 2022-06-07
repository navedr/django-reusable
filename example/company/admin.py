from django.contrib import admin, messages

from .models import Person, Album, Musician
from django_reusable.admin_mixins import EnhancedAdminMixin


class PersonAdmin(EnhancedAdminMixin):
    action_links = [
        ('alert_name', dict(btn_text='Alert Name', btn_class='btn-info', callback=lambda instance: print(instance))),
        ('say_hello', dict(btn_text='Say Hello', btn_class='btn-warning', callback=lambda instance: print("Hello")))
    ]

    list_display = fields = ['first_name', 'last_name', 'alert_name', 'say_hello']


class MusicianAdmin(admin.ModelAdmin):
    pass


class AlbumAdmin(admin.ModelAdmin):
    pass


admin.site.register(Person, PersonAdmin)
admin.site.register(Musician, MusicianAdmin)
admin.site.register(Album, AlbumAdmin)
