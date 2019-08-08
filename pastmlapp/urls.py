from django.conf.urls import url

from pastmlapp import views

app_name = "pastmlapp"

urlpatterns = [
    url(r'^run$', views.pastml, name='pastml'),
    url(r'^$', views.index, name='index'),
    url(r'^run/(?P<id>[a-f0-9-]{32-36})$', views.analysis, name='analysis'),
    url(r'^result/(?P<id>[a-f0-9-]{32-36})$', views.result, name='result'),
    url(r'^result/(?P<id>[a-f0-9-]{32-36})/(?P<full>[0-1])$', views.result, name='result_full'),
    url(r'^view/(?P<id>[a-f0-9-]{32-36})$', views.detail, name='detail'),
    url(r'^view/(?P<id>[a-f0-9-]{32-36})/(?P<full>[0-1])$', views.detail, name='detail_full'),
    url(r'^feedback$', views.feedback, name='feedback'),
    url(r'^help$', views.helppage, name='help'),
    url(r'^cite$', views.cite, name='cite'),
    url(r'^install$', views.install, name='install'),
]
