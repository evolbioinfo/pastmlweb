from django.conf.urls import url

from pastmlapp import views

app_name = "pastmlapp"

urlpatterns = [
    url(r'^run$', views.pastml, name='pastml'),
    url(r'^$', views.index, name='index'),
    url(r'^run/(?P<id>[\w\d-]+)$', views.analysis, name='analysis'),
    url(r'^result_full/(?P<id>[\w\d-]+)$', views.result_full, name='result_full'),
    url(r'^result/(?P<id>[\w\d-]+)$', views.result, name='result'),
    url(r'^view/(?P<id>[\w\d-]+)$', views.detail, name='detail'),
    url(r'^view_full/(?P<id>[\w\d-]+)$', views.detail_full, name='detail_full'),
    url(r'^feedback$', views.feedback, name='feedback'),
    url(r'^help$', views.helppage, name='help'),
    url(r'^cite$', views.cite, name='cite'),
    url(r'^install$', views.install, name='install'),
]
