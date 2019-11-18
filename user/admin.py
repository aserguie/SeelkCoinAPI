from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from user.models import User
from alert.models import Alert


class MyUserAdmin(UserAdmin):
    list_display = ("email", "username", "date_joined", "is_staff", "is_superuser")
    search_fields = ("email", "username")
    readonly_fields = ("date_joined", "last_login")

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.unregister(Group)
admin.site.register(User, MyUserAdmin)
admin.site.register(Alert)
