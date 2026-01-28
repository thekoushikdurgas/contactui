"""
Index URLconf - 8 GET routes.
"""

from django.urls import path
from . import index_views

app_name = 'api_v1_index'
urlpatterns = [
    path('pages/', index_views.index_pages, name='index_pages'),
    path('endpoints/', index_views.index_endpoints, name='index_endpoints'),
    path('relationships/', index_views.index_relationships, name='index_relationships'),
    path('postman/', index_views.index_postman, name='index_postman'),
    path('pages/validate/', index_views.index_pages_validate, name='index_pages_validate'),
    path('endpoints/validate/', index_views.index_endpoints_validate, name='index_endpoints_validate'),
    path('relationships/validate/', index_views.index_relationships_validate, name='index_relationships_validate'),
    path('postman/validate/', index_views.index_postman_validate, name='index_postman_validate'),
]
