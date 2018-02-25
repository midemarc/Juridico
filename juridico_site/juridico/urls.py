from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('question<int:question_id>', views.question),
    path('questions', views.questions),
    path('resultats/<int:reqid>/', views.resultats)
    # path('<int:question_id>/vote/', views.question, name='question'),
]
