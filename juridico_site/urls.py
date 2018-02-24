from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('juridico-site/', include('juridico-site.urls'))
]