from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .models import Question, Category, QuestionFile, AnswerFile
from .forms import QuestionForm, AnswerForm, SearchForm


def get_sidebar_context():
    """Получает контекст для сайдбара"""
    # Получаем категории с количеством вопросов
    categories = Category.objects.annotate(
        question_count=Count('question', filter=Q(question__is_published=True))
    ).order_by('name')

    # Статистика
    total_questions = Question.objects.filter(is_published=True).count()
    answered_count = Question.objects.filter(is_published=True).exclude(answer='').count()
    unanswered_count = total_questions - answered_count

    # Популярные теги
    questions_with_tags = Question.objects.filter(
        is_published=True,
        tags__isnull=False
    ).exclude(tags='')

    tag_counts = {}
    for question in questions_with_tags:
        tags = [tag.strip() for tag in question.tags.split(',') if tag.strip()]
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    popular_tags = sorted(
        [{'name': tag, 'count': count} for tag, count in tag_counts.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:10]

    return {
        'categories': categories,
        'question_count': total_questions,
        'answered_count': answered_count,
        'unanswered_count': unanswered_count,
        'popular_tags': popular_tags,
    }


# Создайте миксин для добавления контекста сайдбара
class SidebarMixin:
    """Миксин для добавления контекста сайдбара"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sidebar_context = get_sidebar_context()
        context.update(sidebar_context)
        return context


# Главная страница
def home(request):
    """Главная страница"""
    recent_questions = Question.objects.filter(
        is_published=True
    ).select_related('category').order_by('-created_at')[:5]

    answered_questions = Question.objects.filter(
        is_published=True
    ).exclude(answer='').order_by('-created_at')[:5]

    # Контекст сайдбара
    sidebar_context = get_sidebar_context()

    context = {
        'recent_questions': recent_questions,
        'answered_questions': answered_questions,
        'form': SearchForm(),
    }
    context.update(sidebar_context)

    return render(request, 'qa_app/home.html', context)


# Список всех вопросов
class QuestionListView(SidebarMixin, ListView):
    """Список всех вопросов"""
    model = Question
    template_name = 'qa_app/question_list.html'
    context_object_name = 'questions'
    paginate_by = 10

    def get_queryset(self):
        queryset = Question.objects.filter(is_published=True).select_related('category')

        # Фильтрация по категории
        category_slug = self.kwargs.get('slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)

        # Сортировка
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['created_at', '-created_at', 'title', 'views']:
            queryset = queryset.order_by(sort_by)

        # Фильтрация по наличию ответа
        answered = self.request.GET.get('answered')
        if answered == 'yes':
            queryset = queryset.exclude(answer='')
        elif answered == 'no':
            queryset = queryset.filter(answer='')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_category'] = self.kwargs.get('slug')
        context['sort_by'] = self.request.GET.get('sort', '-created_at')
        context['answered_filter'] = self.request.GET.get('answered', '')
        context['form'] = SearchForm()
        return context


# Детальная страница вопроса
class QuestionDetailView(SidebarMixin, DetailView):
    """Детальная страница вопроса"""
    model = Question
    template_name = 'qa_app/question_detail.html'
    context_object_name = 'question'

    def get_queryset(self):
        return Question.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()

        # Увеличиваем счетчик просмотров
        question.increment_views()

        # Похожие вопросы
        similar_questions = Question.objects.filter(
            is_published=True
        ).exclude(id=question.id)

        if question.category:
            similar_questions = similar_questions.filter(category=question.category)

        similar_questions = similar_questions.order_by('-created_at')[:5]

        context['similar_questions'] = similar_questions
        context['form'] = SearchForm()
        return context


# Создание нового вопроса
@login_required
def create_question(request):
    """Создание нового вопроса с файлами"""
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user
            question.save()

            # Сохраняем прикрепленные файлы
            files = request.FILES.getlist('attachments')
            for file in files:
                # Проверяем размер файла
                if file.size > 10 * 1024 * 1024:  # 10MB
                    messages.warning(request, f'Файл "{file.name}" превышает лимит 10MB и не был загружен')
                    continue

                QuestionFile.objects.create(
                    question=question,
                    file=file
                )

            if files:
                messages.success(request, f'Вопрос с {len(files)} файлом(ами) успешно добавлен!')
            else:
                messages.success(request, 'Ваш вопрос успешно добавлен!')

            return redirect('qa_app:question_detail', pk=question.pk)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = QuestionForm()

    # Добавляем контекст сайдбара
    sidebar_context = get_sidebar_context()

    return render(request, 'qa_app/question_form.html', {
        'form': form,
        'title': 'Задать новый вопрос',
        **sidebar_context,
    })


# Поиск вопросов
def search_questions(request):
    """Поиск вопросов, включая поиск по файлам"""
    form = SearchForm(request.GET or None)
    questions = Question.objects.filter(is_published=True)

    if form.is_valid():
        query = form.cleaned_data['query']
        search_in = form.cleaned_data.get('search_in', 'all')

        if query:
            # Создаем Q-объекты для поиска
            if search_in == 'all':
                q_objects = (
                        Q(title__icontains=query) |
                        Q(content__icontains=query) |
                        Q(answer__icontains=query) |
                        Q(tags__icontains=query) |
                        Q(files__name__icontains=query) |
                        Q(answer_files__name__icontains=query)
                )
            elif search_in == 'title':
                q_objects = Q(title__icontains=query)
            elif search_in == 'content':
                q_objects = Q(content__icontains=query)
            elif search_in == 'answer':
                q_objects = Q(answer__icontains=query)
            elif search_in == 'tags':
                q_objects = Q(tags__icontains=query)
            elif search_in == 'files':
                q_objects = Q(files__name__icontains=query) | Q(answer_files__name__icontains=query)
            else:
                q_objects = Q(title__icontains=query)

            questions = questions.filter(q_objects).distinct()

    # Пагинация
    paginator = Paginator(questions.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем контекст сайдбара
    sidebar_context = get_sidebar_context()

    return render(request, 'qa_app/search_results.html', {
        'form': form,
        'page_obj': page_obj,
        'query': request.GET.get('query', ''),
        'search_in': request.GET.get('search_in', 'all'),
        **sidebar_context,
    })


@login_required
def delete_file(request, file_type, file_id):
    """Удаление файла"""
    if file_type == 'question':
        file_obj = get_object_or_404(QuestionFile, id=file_id)
        # Проверяем права доступа
        if not (request.user == file_obj.question.author or request.user.is_staff):
            messages.error(request, 'У вас нет прав для удаления этого файла')
            return redirect('qa_app:question_detail', pk=file_obj.question.pk)
    elif file_type == 'answer':
        file_obj = get_object_or_404(AnswerFile, id=file_id)
        # Проверяем права доступа - используем file_obj.question вместо file_obj.answer
        if not (request.user == file_obj.uploaded_by or request.user.is_staff):
            messages.error(request, 'У вас нет прав для удаления этого файла')
            return redirect('qa_app:question_detail', pk=file_obj.question.pk)  # Исправлено: file_obj.question.pk
    else:
        messages.error(request, 'Неверный тип файла')
        return redirect('qa_app:home')

    question_pk = file_obj.question.pk  # Исправлено: всегда используем file_obj.question.pk

    if request.method == 'POST':
        file_obj.delete()
        messages.success(request, 'Файл успешно удален')

    return redirect('qa_app:question_detail', pk=question_pk)


# Добавление ответа
@login_required
def add_answer(request, pk):
    """Редирект на страницу вопроса для использования модального окна"""
    return redirect('qa_app:question_detail', pk=pk)


@login_required
@csrf_exempt
def add_answer_ajax(request, pk):
    """Добавление/редактирование ответа через AJAX с файлами"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Только администраторы могут добавлять ответы'})

    if request.method == 'POST':
        try:
            # Получаем данные из формы
            answer_text = request.POST.get('answer', '').strip()
            files = request.FILES.getlist('attachments')

            if not answer_text:
                return JsonResponse({'success': False, 'error': 'Ответ не может быть пустым'})

            question = Question.objects.get(pk=pk)
            question.answer = answer_text
            question.save()

            # Сохраняем файлы ответа с проверкой размера
            valid_files = []
            for file in files:
                if file.size > 10 * 1024 * 1024:  # 10MB
                    continue  # Пропускаем слишком большие файлы

                AnswerFile.objects.create(
                    question=question,  # Исправлено: связываем с вопросом, а не с ответом
                    file=file,
                    uploaded_by=request.user
                )
                valid_files.append(file.name)

            # Получаем информацию о файлах
            answer_files = []
            for file_obj in question.answer_files.all():  # Используем related_name
                answer_files.append({
                    'id': file_obj.id,
                    'name': file_obj.name,
                    'url': file_obj.file.url,
                    'icon': file_obj.get_file_icon(),
                    'size': file_obj.get_file_size()
                })

            response_data = {
                'success': True,
                'message': 'Ответ успешно сохранен',
                'answer': question.answer,
                'updated_at': question.updated_at.strftime('%d.%m.%Y %H:%M'),
                'files': answer_files
            }

            if len(valid_files) < len(files):
                response_data['warning'] = 'Некоторые файлы превышают лимит 10MB и не были загружены'

            return JsonResponse(response_data)

        except Question.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Вопрос не найден'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})
