from django.urls import path, include
from club.views.main import ClubApiViewSet


urlpatterns = [
    path('', ClubApiViewSet.as_view({'get': "get_all"})),
    path('<int:club_id>/', ClubApiViewSet.as_view({
        'get': 'get_by_id'
    })),
]