from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Developer, Property, PropertyImage, PropertyVideo, Blog, Notification, Contact, Service


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_email', 'contact_phone', 'created_at']
    search_fields = ['name', 'contact_email']


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ['image', 'caption', 'order']
    verbose_name = "Property Image"
    verbose_name_plural = "Property Images (Gallery)"


class PropertyVideoInline(admin.TabularInline):
    model = PropertyVideo
    extra = 1
    fields = ['video', 'title', 'caption', 'order']
    verbose_name = "Property Video"
    verbose_name_plural = "Property Videos"


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'property_type', 'city', 'price', 'is_published', 'featured', 'created_at']
    list_filter = ['property_type', 'is_published', 'featured', 'city', 'developer']
    search_fields = ['title', 'city', 'location', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published', 'featured']
    inlines = [PropertyImageInline, PropertyVideoInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'property_type', 'developer', 'description')
        }),
        ('Location', {
            'fields': ('city', 'location', 'latitude', 'longitude')
        }),
        ('Details', {
            'fields': ('price', 'carpet_area', 'floor_number', 'total_floors', 'possession_date', 'loan_approved_by')
        }),
        ('Main Media', {
            'fields': ('image', 'video'),
            'description': 'Primary image and video. Add more in the galleries below.'
        }),
        ('Contact Info (User Submitted)', {
            'fields': ('contact_name', 'contact_email', 'contact_phone', 'user_type'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_published', 'featured')
        }),
    )


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_published', 'created_at']
    list_filter = ['is_published', 'author']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'subject']
    list_editable = ['is_active']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'created_at']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
