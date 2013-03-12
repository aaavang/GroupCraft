from django.conf.urls import patterns, url

from groupcraft import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^about/$', views.about, name='about'),
	url(r'^group/(?P<group_name_url>.+)', views.group, name='group'),
	url(r'^remove/(?P<username>\w+)/(?P<group_name_url>.+)', views.remove, name='remove'),
	url(r'^post/(?P<group_name_url>\w+)', views.ajax_post, name='post'),
	url(r'^tag/(?P<tag_name>.+)', views.tag, name='tag'),
	url(r'^add_group/', views.add_group, name='add group'),
	url(r'^edit_group/', views.edit_group, name='edit group'),
	url(r'^register/$', views.register, name='register'),
	url(r'^login/$', views.user_login, name='login'),
	url(r'^logout/$', views.user_logout, name='logout'),
	url(r'^search/$', views.search, name='search'),
	url(r'^flip/$', views.flip, name='flip'),
	url(r'^browse/$', views.browse, name='browse'),
	url(r'^user/(?P<username>\w+$)', views.user, name='user'),
	url(r'^join_group/(?P<group_name_url>\w+)', views.join_group, name='join_group'),
	url(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/imgs/favicon.ico'}),

)

