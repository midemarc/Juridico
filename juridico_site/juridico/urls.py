from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('question', views.question),
    # path('<int:question_id>/vote/', views.question, name='question'),
]