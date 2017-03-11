from django.conf.urls import url, include, handler403
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('record.urls'))
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'record.views.http_403_permission_denied'
handler404 = 'record.views.http_404_not_found'
handler500 = 'record.views.http_500_server_error'
