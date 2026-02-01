from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .models import Question, Category, AttachedFile, Tag
from .forms import QuestionForm, AnswerForm, SearchForm, LoginForm
from django.template.defaulttags import register
from django.utils import timezone
from django.db import models


@register.filter
def divisibleby(value, arg):
    """Деление для шаблона"""
    try:
        return int(value) / int(arg) * 100
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def multiply(value, arg):
    """Умножание для шаблона"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


def get_sidebar_context():
    """Получает контекст для сайдбара"""
    categories = Category.objects.annotate(
        question_count=Count('question', filter=Q(question__is_published=True))
    ).order_by('name')

    total_questions = Question.objects.filter(is_published=True).count()
    answered_count = Question.objects.filter(is_published=True).exclude(answer='').count()
    unanswered_count = total_questions - answered_count

    # Популярные теги
    questions_with_tags = Question.objects.filter(
        is_published=True
    ).prefetch_related('tags')

    tag_counts = {}
    for question in questions_with_tags:
        for tag in question.tags.all():
            tag_name = tag.name.lower().strip()
            tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1

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


class CustomLoginView(LoginView):
    template_name = 'qa_app/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_sidebar_context())
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Добро пожаловать, {form.get_user().username}!')
        return super().form_valid(form)


def logout_view(request):
    from django.contrib.auth import logout
    if request.user.is_authenticated:
        messages.info(request, 'Вы успешно вышли из системы.')
    logout(request)
    return redirect('qa_app:home')


class SidebarMixin:
    """Миксин для добавления контекста сайдбара"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sidebar_context = get_sidebar_context()
        context.update(sidebar_context)
        return context


class QuestionListView(SidebarMixin, ListView):
    model = Question
    template_name = 'qa_app/question_list.html'
    context_object_name = 'questions'
    paginate_by = 12

    def get_queryset(self):
        queryset = Question.objects.filter(is_published=True).select_related('category')

        category_slug = self.kwargs.get('slug')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                queryset = queryset.filter(category=category)
                self.current_category = category
            except Category.DoesNotExist:
                self.current_category = None
        else:
            self.current_category = None

        answered = self.request.GET.get('answered')
        if answered == 'yes':
            queryset = queryset.exclude(answer='')
        elif answered == 'no':
            queryset = queryset.filter(answer='')

        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['created_at', '-created_at', 'title', '-title', 'views']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_category'] = getattr(self, 'current_category', None)
        context['sort_by'] = self.request.GET.get('sort', '-created_at')
        context['answered_filter'] = self.request.GET.get('answered', '')
        context['form'] = SearchForm()
        context['today'] = timezone.now()
        return context


class QuestionDetailView(SidebarMixin, DetailView):
    model = Question
    template_name = 'qa_app/question_detail.html'
    context_object_name = 'question'

    def get_queryset(self):
        return Question.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()
        question.increment_views()

        similar_questions = Question.objects.filter(
            is_published=True
        ).exclude(id=question.id)

        if question.category:
            similar_questions = similar_questions.filter(category=question.category)

        similar_questions = similar_questions.order_by('-created_at')[:5]

        context['similar_questions'] = similar_questions
        context['form'] = SearchForm()

        # Добавляем все прикреплённые файлы
        context['attached_files'] = AttachedFile.objects.filter(
            content_type__model='question',
            object_id=question.pk
        )

        # Для удобства в шаблоне
        context['today'] = timezone.now()

        return context


@login_required
def create_question(request):
    """Создание нового вопроса с файлами"""
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user
            question.save()

            files = request.FILES.getlist('attachments')
            for file in files:
                AttachedFile.objects.create(
                    content_object=question,
                    file=file,
                    uploaded_by=request.user
                )

            messages.success(request, 'Ваш вопрос успешно добавлен!')
            return redirect('qa_app:question_detail', pk=question.pk)
    else:
        form = QuestionForm()

    sidebar_context = get_sidebar_context()

    return render(request, 'qa_app/question_form.html', {
        'form': form,
        'title': 'Задать новый вопрос',
        **sidebar_context,
    })


def search_questions(request):
    """Поиск вопросов"""
    form = SearchForm(request.GET or None)
    questions = Question.objects.filter(is_published=True)

    if form.is_valid():
        query = form.cleaned_data['query']
        search_in = form.cleaned_data.get('search_in', 'all')

        if query:
            if search_in == 'all':
                q_objects = (
                        Q(title__icontains=query) |
                        Q(content__icontains=query) |
                        Q(answer__icontains=query) |
                        Q(tags__name__icontains=query) |
                        Q(attachedfile__name__icontains=query)
                )
            elif search_in == 'title':
                q_objects = Q(title__icontains=query)
            elif search_in == 'content':
                q_objects = Q(content__icontains=query)
            elif search_in == 'answer':
                q_objects = Q(answer__icontains=query)
            elif search_in == 'tags':
                q_objects = Q(tags__name__icontains=query)
            elif search_in == 'files':
                q_objects = Q(attachedfile__name__icontains=query)
            else:
                q_objects = Q(title__icontains=query)

            questions = questions.filter(q_objects).distinct()

    paginator = Paginator(questions.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sidebar_context = get_sidebar_context()

    return render(request, 'qa_app/search_results.html', {
        'form': form,
        'page_obj': page_obj,
        'query': request.GET.get('query', ''),
        'search_in': request.GET.get('search_in', 'all'),
        **sidebar_context,
    })


@login_required
@csrf_exempt
def add_answer_ajax(request, pk):
    """Добавление/редактирование/удаление ответа через AJAX"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Только администраторы могут управлять ответами'})

    try:
        question = Question.objects.get(pk=pk)

        if request.method == 'POST':
            # Проверяем, содержит ли запрос файлы (multipart/form-data)
            if request.content_type.startswith('multipart/form-data'):
                answer_text = request.POST.get('answer', '').strip()
                action = request.POST.get('action')
            else:
                # Обычный JSON-запрос
                try:
                    body = request.body.decode('utf-8', errors='replace')
                    data = json.loads(body)
                    answer_text = data.get('answer', '').strip()
                    action = data.get('action')
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'error': 'Некорректные данные: ожидается JSON'})

            # Если это удаление ответа
            if action == 'delete_answer':
                question.answer = ''
                question.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Ответ успешно удалён',
                    'answer': '',
                    'updated_at': question.updated_at.strftime('%d.%m.%Y %H:%M'),
                })

            # Обычное сохранение ответа
            if not answer_text:
                return JsonResponse({'success': False, 'error': 'Ответ не может быть пустым'})

            question.answer = answer_text
            question.save()

            # Обработка вложений (если они есть)
            files = request.FILES.getlist('attachments')
            for file in files:
                AttachedFile.objects.create(
                    content_object=question,
                    file=file,
                    uploaded_by=request.user
                )

            return JsonResponse({
                'success': True,
                'message': 'Ответ успешно сохранён',
                'answer': question.answer,
                'updated_at': question.updated_at.strftime('%d.%m.%Y %H:%M'),
            })

        return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

    except Question.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Вопрос не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_file(request, file_id):
    file_obj = get_object_or_404(AttachedFile, id=file_id)
    content_object = file_obj.content_object

    # Проверка прав
    can_delete = (
        (hasattr(content_object, 'author') and content_object.author == request.user) or
        (file_obj.uploaded_by == request.user) or
        request.user.is_staff
    )
    if not can_delete:
        messages.error(request, "Нет прав на удаление.")
        return redirect('qa_app:home')

    redirect_url = content_object.get_absolute_url()

    if request.method == "POST":
        file_path = None
        if file_obj.file:
            file_path = file_obj.file.path

        try:
            file_obj.delete()  # Удаление объекта → должен сработа сигнал

            # Дополнительно: если файл остался — удаляем вручную
            if file_path and os.path.isfile(file_path):
                os.remove(file_path)
                print(f"📁 Ручное удаление файла: {file_path}")

            messages.success(request, "Файл успешно удалён.")
        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)}")
            print(f"❌ Ошибка при удалении: {e}")

    return redirect(redirect_url)


def home(request):
    # Последние вопросы
    recent_questions = Question.objects.filter(is_published=True)\
                                    .select_related('author', 'category')\
                                    .prefetch_related('tags')[:6]

    # Популярные (с ответами и высоким количеством просмотров)
    answered_questions = Question.objects.filter(
        is_published=True,
        answer__isnull=False
    ).exclude(answer__exact='')\
     .order_by('-views')[:6]

    # Категории
    categories = Category.objects.annotate(
        question_count=models.Count('question', filter=models.Q(question__is_published=True))
    ).order_by('name')

    # Статистика
    total_questions = Question.objects.filter(is_published=True).count()
    answered_count = answered_questions.count()

    context = {
        'recent_questions': recent_questions,
        'answered_questions': answered_questions,
        'categories': categories,
        'question_count': total_questions,
        'answered_count': answered_count,
        'popular_tags': Tag.objects.all()[:10],  # пример
    }

    return render(request, 'qa_app/home.html', context)