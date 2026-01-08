from django.urls import path
from .views import signup_view, CustomLoginView, logout_view, dashboard_view,staff_dashboard_view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('staff-dashboard/',staff_dashboard_view, name='staff_dashboard'),
]
