from django.urls import path, include
from .api.urls import urlpatterns as api_urls
from .templates.urls import urlpatterns as templates_urls


urlpatterns = [
    path('', include(templates_urls)),
    path('api/', include(api_urls)),
]