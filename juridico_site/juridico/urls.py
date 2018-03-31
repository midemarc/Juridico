from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('questions', views.antique_question),
    path('resultats/<int:reqid>/', views.antique_resultats),
    path('requete/client<int:cid>', views.antique_question),
    # path('<int:question_id>/vote/', views.question, name='question'),
    path('api/questions<int:question_id>', views.api_question),
    path('api/questions', views.api_questions),
    path('api/reponses', views.api_reponses),
    # path('api/next_question<int:reponse_id> <ìnt:request_id>', views.api_next_question),
    path('api/next_question', views.api_next_question),
<<<<<<< HEAD
    path('antique/questions', views.antique_question),
    path('antique/resultats', views.antique_resultats)
=======
    path('api/resultats', views.api_resultats),
>>>>>>> 0f01d15f54f08262877bac0adf6155cb24fe6728
]
