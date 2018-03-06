from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('question<int:question_id>', views.question),
    path('questions', views.questions),
    path('resultats/<int:reqid>/', views.resultats),
    path('requete/client<int:cid>', views.requete),
    # path('<int:question_id>/vote/', views.question, name='question'),
    path('api/questions(<int:question_id>)', views.api_question),
    path('api/questions', views.api_questions)
]
