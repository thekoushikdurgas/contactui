"""Django admin configuration for Durgasman app."""

from django.contrib import admin
from .models import Collection, ApiRequest, Environment, EnvVariable, RequestHistory, MockEndpoint


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(ApiRequest)
class ApiRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'method', 'collection', 'created_at']
    list_filter = ['method', 'collection', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(EnvVariable)
class EnvVariableAdmin(admin.ModelAdmin):
    list_display = ['key', 'environment', 'enabled']
    list_filter = ['environment', 'enabled']
    search_fields = ['key', 'value']


@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ['method', 'url', 'response_status', 'response_time_ms', 'timestamp']
    list_filter = ['method', 'response_status', 'timestamp']
    search_fields = ['url', 'method']
    readonly_fields = ['timestamp']


@admin.register(MockEndpoint)
class MockEndpointAdmin(admin.ModelAdmin):
    list_display = ['method', 'path', 'status_code', 'enabled', 'collection']
    list_filter = ['method', 'status_code', 'enabled', 'collection']
    search_fields = ['path']
    readonly_fields = ['created_at']