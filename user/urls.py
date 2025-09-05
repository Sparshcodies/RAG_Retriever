from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_ui, name='chat_ui'),
    path('api/ingest', views.ingest, name='ingest_data'),
    path('api/query', views.query, name='get_users'),
    path('api/ingest-file', views.ingest_file, name='ingest_file'),
    path('api/download-file', views.download_file, name='download_file'),
]
