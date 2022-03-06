from django.urls import path
from . import views

urlpatterns = [
    path('metadata/', views.metadata, name="metadata"),
    path('classes/', views.classes, name="classes"),
    path('results/', views.results, name="results"),
    path('inspection/', views.inspection, name="inspection"),
    path('instructions/', views.instructions, name="instructions"),
    path('feedback/', views.feedback, name="feedback"),
]
