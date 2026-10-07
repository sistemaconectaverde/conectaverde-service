from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.accounts.models import User
from apps.productions.models import UserProductionPermission


class CVUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "name", "role")


class CVUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


class ProductionPermissionInline(admin.TabularInline):
    model = UserProductionPermission
    fk_name = "user"
    extra = 0
    autocomplete_fields = ["production"]
    fields = ("production", "department", "granted_by", "created_at")
    readonly_fields = ("created_at",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CVUserChangeForm
    add_form = CVUserCreationForm
    inlines = [ProductionPermissionInline]

    list_display = ("email", "name", "role", "is_active", "last_login")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "name")
    ordering = ("name",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Perfil", {"fields": ("name", "role")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "role", "password1", "password2")}),
    )
