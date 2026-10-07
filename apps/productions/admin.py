from django.contrib import admin

from apps.productions.models import Production, UserProductionPermission


class PermissionInline(admin.TabularInline):
    model = UserProductionPermission
    fk_name = "production"
    extra = 0
    autocomplete_fields = ["user"]
    fields = ("user", "department", "granted_by", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "client_name", "city", "status", "is_active")
    list_filter = ("status", "is_active")
    search_fields = ("name", "code", "client_name")
    prepopulated_fields = {"code": ("name",)}
    inlines = [PermissionInline]


@admin.register(UserProductionPermission)
class UserProductionPermissionAdmin(admin.ModelAdmin):
    list_display = ("user", "production", "department", "created_at")
    list_filter = ("department", "production")
    search_fields = ("user__email", "production__name")
    autocomplete_fields = ["user", "production"]
