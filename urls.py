from django.conf.urls import url

from pastmlapp import views

app_name = "pastmlapp"

urlpatterns = [
    url(r'^$', views.index, name='index'),
    # ex: /pastmlapp/5/
    url(r'^(?P<id>\d+)/$', views.detail, name='detail'),
    # ex: /pastmlapp/5/results/
    url(r'^(?P<id>\d+)/results/$', views.results, name='results'),
    url(r'^pastml$', views.pastml, name='pastml'),
    url(r'^analysis/(?P<id>\d+)$', views.analysis, name='analysis'),
    url(r'^feedback$', views.feedback, name='feedback'),
]
