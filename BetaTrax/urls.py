from django.urls import path
from . import views

# Create your tests here.
urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.LoginView.as_view(), name="login"),
    path('report/', views.ReportView.as_view(), name="report"),
]