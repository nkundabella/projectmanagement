from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('trackera.urls')),
    path('trackera/', include('trackera.urls')),
    path('camellia/', include('camellia.urls')),
]