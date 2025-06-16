from django.contrib import admin
from django.urls import path, include
from presentation.urls import urlpatterns as all_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(all_urls))
]
