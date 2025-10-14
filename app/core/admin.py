"""Django Admin customization"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core import models


class UserAdmin(BaseUserAdmin):
    list_display = ["email", "name"]
    ordering = ["id"]
    fieldsets = (
        (None, {
            "fields": (
                "email",
                "name",
                "password",
                "last_login",
            ),
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        }),
    )
    readonly_fields = ["last_login"]
    add_fieldsets = (
        (None, {
            "fields": (
                "email",
                "name",
                "password",
                "password2",
            ),
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe)
admin.site.register(models.Tag)
