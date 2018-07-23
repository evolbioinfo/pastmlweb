from django.conf.urls import url

from pastmlapp import views

app_name = "pastmlapp"

urlpatterns = [
    url(r'^run$', views.pastml, name='pastml'),
    url(r'^$', views.index, name='index'),
    url(r'^run/(?P<id>[\d\w-]+)$', views.analysis, name='analysis'),
    url(r'^result/(?P<id>[\d\w-]+)$', views.result, name='result'),
    url(r'^view/(?P<id>[\d\w-]+)/$', views.detail, name='detail'),
    url(r'^feedback$', views.feedback, name='feedback'),
    url(r'^help$', views.helppage, name='help'),
    url(r'^cite$', views.cite, name='cite'),
    url(r'^install$', views.install, name='install'),
]
