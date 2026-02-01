from django.urls import path
from . import views
from .views import CustomLoginView

app_name = 'qa_app'

urlpatterns = [
    # Главная и навигация
    path('', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Вопросы
    path('questions/', views.QuestionListView.as_view(), name='question_list'),
    path('questions/category/<slug:slug>/', views.QuestionListView.as_view(), name='category_questions'),
    path('questions/<int:pk>/', views.QuestionDetailView.as_view(), name='question_detail'),
    path('questions/create/', views.create_question, name='create_question'),

    path('question/<int:pk>/delete/', views.delete_question, name='delete_question'),

    # Поиск
    path('search/', views.search_questions, name='search_questions'),

    # Ответы (AJAX)
    path('questions/<int:pk>/add-answer-ajax/', views.add_answer_ajax, name='add_answer_ajax'),

    # Удаление файлов
    path('files/delete/<int:file_id>/', views.delete_file, name='delete_file'),

    # Задачи (новое)
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),

    # Записи по задаче
    path('tasks/<int:task_pk>/notes/add/', views.TaskNoteCreateView.as_view(), name='tasknote_create'),
    path('tasks/<int:task_pk>/notes/<int:pk>/edit/', views.TaskNoteUpdateView.as_view(), name='tasknote_update'),
    path('tasks/<int:task_pk>/notes/<int:pk>/delete/', views.TaskNoteDeleteView.as_view(), name='tasknote_delete'),

    # Прикрепление файлов к задаче или записи
    path('tasks/<int:task_pk>/attach/', views.AttachedFileCreateView.as_view(), name='attach_file_to_task'),
    path('notes/<int:note_pk>/attach/', views.AttachedFileCreateView.as_view(), name='attach_file_to_note'),
]