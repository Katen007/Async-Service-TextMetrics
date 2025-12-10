from django.urls import path
from app import views

urlpatterns = [
    path('calculate_readability/', views.perform_calculation, name='calc'),
]