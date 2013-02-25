from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^groupcraft/', include('groupcraft.urls')),
                       url(r'^admin/', include(admin.site.urls)),
                       )