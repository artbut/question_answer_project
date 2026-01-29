from django.urls import path
from . import views

app_name = 'qa_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('questions/', views.QuestionListView.as_view(), name='question_list'),
    path('questions/category/<slug:slug>/',
         views.QuestionListView.as_view(),
         name='category_questions'),
    path('questions/<int:pk>/',
         views.QuestionDetailView.as_view(),
         name='question_detail'),
    path('questions/create/',
         views.create_question,
         name='create_question'),
    path('search/',
         views.search_questions,
         name='search_questions'),
    path('questions/<int:pk>/add-answer-ajax/',
         views.add_answer_ajax,
         name='add_answer_ajax'),
    path('files/delete/<str:file_type>/<int:file_id>/',
         views.delete_file,
         name='delete_file'),
]