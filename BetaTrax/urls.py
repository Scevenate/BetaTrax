from django.urls import path
from . import views

# Create your tests here.
urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.LoginView.as_view(), name="login"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
    path('report/', views.ReportsView.as_view(), name="reports"),
    path('report/<int:id>/', views.ReportView.as_view(), name="report"),
]