from django.urls import path

from . import views

app_name = 'web'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('system/save-page-screenshot/', views.save_page_screenshot, name='save_page_screenshot'),
    path('catalog/', views.catalog, name='catalog'),
    path('books/<int:id>/', views.book_detail, name='book_detail'),
    path('copies/<int:id>/', views.copy_detail, name='copy_detail'),
    path('events/', views.events_feed, name='events'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('notifications/', views.notifications_page, name='notifications'),
    path('profile/', views.profile, name='profile'),
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/register/', views.auth_register, name='auth_register'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('scan/', views.scan_placeholder, name='scan'),
]
