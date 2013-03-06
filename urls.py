from django.conf.urls import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^groupcraft/', include('groupcraft.urls')),
                       url(r'^admin/', include(admin.site.urls)),
                       )
if settings.DEBUG:
	# static files (images, css, javascript, etc.)
	urlpatterns += patterns('',
	                        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
		                        'document_root': settings.MEDIA_ROOT}))