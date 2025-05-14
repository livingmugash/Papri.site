# backend/api/urls.py
from django.urls import path
from .views import VideoSearchView, SearchStatusView, SearchResultsView

urlpatterns = [
    path('search/', VideoSearchView.as_view(), name='video_search'),
    path('search/status/<str:task_id>/', SearchStatusView.as_view(), name='search_status'),
    path('search/results/<str:task_id>/', SearchResultsView.as_view(), name='search_results'),
]
