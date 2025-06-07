from django.urls import path

from club.views.templates import ClubTemplatesViewSet

urlpatterns = [
    path('', ClubTemplatesViewSet.as_view({'get': 'get_lending'})),
    path('club/<int:club_id>/', ClubTemplatesViewSet.as_view({'get': 'get_page'}))
]