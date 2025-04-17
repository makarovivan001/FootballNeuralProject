from django.urls import path, include
from .api.urls import urlpatterns as api_urls


urlpatterns = [
    path('api/', include(api_urls))
]