from django.urls import path

from club.views.templates import ClubTemplatesViewSet

urlpatterns = [
    path('', ClubTemplatesViewSet.as_view({'get': 'get_lending'})),
    path('club/', ClubTemplatesViewSet.as_view({'get': 'get_page'}))
]