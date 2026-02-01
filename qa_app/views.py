from venv import logger
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from django.utils.decorators import method_decorator
import json
import os
from django.contrib.contenttypes.models import ContentType
from .models import Question, Category, AttachedFile, Tag, Task, TaskNote, SearchQuery
from .forms import QuestionForm, SearchForm, LoginForm
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

    # Добавлено: количество задач и последние задачи
    total_tasks = Task.objects.count()
    recent_tasks = Task.objects.select_related('author').order_by('-created_at')[:5]

    return {
        'categories': categories,
        'question_count': total_questions,
        'answered_count': answered_count,
        'unanswered_count': unanswered_count,
        'popular_tags': popular_tags,
        'sidebar_total_tasks': total_tasks,
        'sidebar_recent_tasks': recent_tasks,
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

        sort_by = self.request.GET.get('schedule', '-created_at')
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


@user_passes_test(lambda u: u.is_staff)
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Вопрос успешно удалён.')
        return redirect('qa_app:question_list')
    return redirect('qa_app:question_detail', pk=pk)


def search_questions(request):
    """
    Представление для поиска по вопросам и ответам.
    Поддерживает поиск по заголовкам, содержанию, тегам и ответам.
    Сохраняет каждый запрос в модель SearchQuery для анализа популярных тем.
    """
    query = request.GET.get('query', '').strip()
    search_in = request.GET.get('search_in', 'all')  # all, title, content, tags

    # Словарь для передачи в шаблон
    context = {
        'query': query,
        'search_in': search_in,
        'page_obj': None,
        'popular_searches': [],
    }

    # Если есть запрос — выполняем поиск
    if query:
        # Формируем Q-объекты для разных полей
        q_objects = []

        if search_in == 'title':
            q_objects.append(Q(title__icontains=query))
        elif search_in == 'content':
            q_objects.append(Q(content__icontains=query) | Q(answer__icontains=query))
        elif search_in == 'tags':
            q_objects.append(Q(tags__name__icontains=query))
        else:  # 'all' — поиск везде
            q_objects.append(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(answer__icontains=query) |
                Q(tags__name__icontains=query)
            )

        # Выполняем запрос
        questions = Question.objects.filter(
            is_published=True
        ).filter(*q_objects).distinct().select_related(
            'category', 'author'
        ).prefetch_related('tags').order_by('-created_at')

        # Пагинация
        paginator = Paginator(questions, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj

        # Сохраняем поисковый запрос в базу
        try:
            SearchQuery.objects.create(
                term=query,
                user=request.user if request.user.is_authenticated else None,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to save search query '{query}': {e}")

    # Добавляем популярные поисковые запросы (последние 30 дней)
    try:
        from django.utils import timezone
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        popular_searches = SearchQuery.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('term').annotate(
            count=Count('term')
        ).order_by('-count')[:10]

        context['popular_searches'] = popular_searches
    except:
        pass  # Игнорируем ошибки при получении популярных запросов

    return render(request, 'qa_app/search_results.html', context)


def get_client_ip(request):
    """
    Получает реальный IP-адрес клиента из HTTP-заголовков.
    Учитывает прокси (X-Forwarded-For, X-Real-IP).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For может содержать список IP через запятую
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
@csrf_exempt
def add_answer_ajax(request, pk):
    """
    Добавление/редактирование/удаление ответа через AJAX.
    Поддерживает:
    - multipart/form-data (с файлами)
    - application/json (без файлов)
    - удаление ответа
    - валидацию прав доступа
    """
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Только администраторы могут управлять ответами'
        }, status=403)

    try:
        question = Question.objects.select_related('author').get(pk=pk)
    except Question.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Вопрос не найден'
        }, status=404)

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Неверный метод запроса'
        }, status=405)

    # Определяем тип запроса: multipart или JSON
    if request.content_type.startswith('multipart/form-data'):
        answer_text = request.POST.get('answer', '').strip()
        action = request.POST.get('action')
        files = request.FILES.getlist('attachments')
    else:
        try:
            body = request.body.decode('utf-8', errors='replace')
            data = json.loads(body)
            answer_text = data.get('answer', '').strip()
            action = data.get('action')
            files = []
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Некорректные данные: ожидается JSON ({str(e)})'
            }, status=400)

    # Удаление ответа
    if action == 'delete_answer':
        question.answer = ''
        question.save(update_fields=['answer', 'updated_at'])

        # Логируем удаление ответа
        logger.info(f"Answer deleted by {request.user.username} for question {question.pk}")

        return JsonResponse({
            'success': True,
            'message': 'Ответ удалён',
            'answer': '',
            'has_answer': False,
            'updated_at': timezone.localtime(question.updated_at).strftime('%d.%m.%Y %H:%M'),
            'answer_author': None
        })

    # Проверка на пустой ответ
    if not answer_text.strip():
        return JsonResponse({
            'success': False,
            'error': 'Ответ не может быть пустым'
        }, status=400)

    # Сохраняем ответ
    question.answer = answer_text
    question.save(update_fields=['answer', 'updated_at'])

    # Обработка файлов
    saved_files = []
    for file in files:
        # Валидация размера файла (макс 10MB)
        if file.size > 10 * 1024 * 1024:
            continue

        attached_file = AttachedFile.objects.create(
            content_object=question,
            file=file,
            uploaded_by=request.user
        )
        saved_files.append({
            'id': attached_file.id,
            'name': attached_file.name,
            'url': attached_file.file.url,
            'size': attached_file.get_file_size(),
            'icon': attached_file.get_file_icon(),
            'uploaded_by': request.user.username,
            'uploaded_at': timezone.localtime(attached_file.uploaded_at).strftime('%d.%m.%Y %H:%M')
        })

    # Логируем обновление ответа
    logger.info(f"Answer updated by {request.user.username} for question {question.pk}")

    return JsonResponse({
        'success': True,
        'message': 'Ответ сохранён',
        'answer': question.answer,
        'has_answer': True,
        'updated_at': timezone.localtime(question.updated_at).strftime('%d.%m.%Y %H:%M'),
        'answer_author': {
            'username': request.user.username,
            'is_staff': request.user.is_staff
        },
        'files': saved_files,
        'total_files': AttachedFile.objects.filter(
            content_type__model='question',
            object_id=question.pk
        ).count()
    })


@login_required
def delete_file(request, file_id):
    """Удаляет прикреплённый файл. Только POST."""
    file_obj = get_object_or_404(AttachedFile, id=file_id)
    content_object = file_obj.content_object

    # Проверка прав
    can_delete = (
            (hasattr(content_object, 'author') and content_object.author == request.user) or
            (file_obj.uploaded_by == request.user) or
            request.user.is_staff
    )
    if not can_delete:
        messages.error(request, "У вас нет прав для удаления этого файла.")
        return redirect('qa_app:home')

    # Сохраняем URL до удаления объекта
    redirect_url = getattr(content_object, 'get_absolute_url', lambda: reverse('qa_app:home'))()

    if request.method == "POST":
        file_path = file_obj.file.path if file_obj.file else None
        try:
            file_obj.delete()  # Удалит и физический файл через сигнал
            messages.success(request, "Файл успешно удалён.")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)  # Резервное удаление
        except Exception as e:
            messages.error(request, f"Ошибка при удалении: {str(e)}")

    return redirect(redirect_url)


def home(request):
    recent_questions = Question.objects.filter(is_published=True) \
        .select_related('author', 'category') \
        .prefetch_related('tags')[:6]

    answered_questions = Question.objects.filter(
        is_published=True,
        answer__isnull=False
    ).exclude(answer__exact='') \
        .order_by('-views')[:6]

    categories = Category.objects.annotate(
        question_count=models.Count('question', filter=models.Q(question__is_published=True))
    ).order_by('name')

    total_questions = Question.objects.filter(is_published=True).count()
    answered_count = answered_questions.count()

    # Добавляем актуальную статистику по задачам
    total_tasks = Task.objects.count()
    recent_tasks = Task.objects.select_related('author').order_by('-created_at')[:5]

    context = {
        'recent_questions': recent_questions,
        'answered_questions': answered_questions,
        'categories': categories,
        'question_count': total_questions,
        'answered_count': answered_count,
        'popular_tags': Tag.objects.all()[:10],

        # Передаём данные для сайдбара
        'sidebar_total_tasks': total_tasks,
        'sidebar_recent_tasks': recent_tasks,
        'sidebar_question_count': total_questions,
        'sidebar_answered_count': answered_count,
        'sidebar_unanswered_count': total_questions - answered_count,
        'sidebar_categories': categories,
        'sidebar_popular_tags': Tag.objects.all()[:10],
    }

    return render(request, 'qa_app/home.html', context)


# ----------------------------
# ЗАДАЧИ (Task)
# ----------------------------

class TaskListView(SidebarMixin, ListView):
    model = Task
    template_name = 'qa_app/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        return Task.objects.select_related('author', 'question').all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавляем статистику по задачам
        total_tasks = self.get_queryset().count()
        last_week = timezone.now() - timedelta(days=7)
        recent_count = self.get_queryset().filter(created_at__gte=last_week).count()

        context.update({
            'total_tasks': total_tasks,
            'recent_count': recent_count,
        })
        return context


class TaskDetailView(SidebarMixin, DetailView):
    model = Task
    template_name = 'qa_app/task_detail.html'
    context_object_name = 'task'


class TaskCreateView(SidebarMixin, CreateView):
    model = Task
    fields = ['title', 'description', 'question']
    template_name = 'qa_app/task_form.html'
    success_url = reverse_lazy('qa_app:task_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Задача создана.')
        return super().form_valid(form)


class TaskUpdateView(SidebarMixin, UpdateView):
    model = Task
    fields = ['title', 'description', 'question']
    template_name = 'qa_app/task_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Задача обновлена.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('qa_app:task_detail', kwargs={'pk': self.object.pk})


class TaskDeleteView(SidebarMixin, DeleteView):
    model = Task
    template_name = 'qa_app/task_confirm_delete.html'
    success_url = reverse_lazy('qa_app:task_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Задача удалена.')
        return super().delete(request, *args, **kwargs)


# ----------------------------
# ЗАПИСИ ПО ЗАДАЧЕ (TaskNote)
# ----------------------------

class TaskNoteCreateView(SidebarMixin, CreateView):
    model = TaskNote
    fields = ['title', 'content', 'order']
    template_name = 'qa_app/tasknote_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(Task, pk=kwargs['task_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.task = self.task
        form.instance.author = self.request.user
        messages.success(self.request, 'Запись добавлена.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task'] = self.task  # ← обязательно!
        return context

    def get_success_url(self):
        return reverse('qa_app:task_detail', kwargs={'pk': self.task.pk})


class TaskNoteUpdateView(SidebarMixin, UpdateView):
    model = TaskNote
    fields = ['title', 'content', 'order']
    template_name = 'qa_app/tasknote_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Запись обновлена.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('qa_app:task_detail', kwargs={'pk': self.object.task.pk})


class TaskNoteDeleteView(SidebarMixin, DeleteView):
    model = TaskNote
    template_name = 'qa_app/tasknote_confirm_delete.html'

    def get_success_url(self):
        task_pk = self.object.task.pk
        messages.success(self.request, 'Запись удалена.')
        return reverse('qa_app:task_detail', kwargs={'pk': task_pk})


# ----------------------------
# ПРИКРЕПЛЕНИЕ ФАЙЛОВ
# ----------------------------

class AttachedFileCreateView(SidebarMixin, CreateView):
    model = AttachedFile
    fields = ['file', 'name']
    template_name = 'qa_app/attach_file.html'

    def dispatch(self, request, *args, **kwargs):
        self.task_pk = kwargs.get('task_pk')
        self.note_pk = kwargs.get('note_pk')

        if self.task_pk:
            self.content_object = get_object_or_404(Task, pk=self.task_pk)
        elif self.note_pk:
            self.content_object = get_object_or_404(TaskNote, pk=self.note_pk)
        else:
            raise Http404("Объект не указан.")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_object'] = self.content_object
        # Явно передаём task_pk в контекст для шаблона
        if self.task_pk:
            context['task_pk'] = self.task_pk
        elif self.note_pk and hasattr(self.content_object, 'task'):
            context['task_pk'] = self.content_object.task.pk
        else:
            context['task_pk'] = None
        return context

    def form_valid(self, form):
        form.instance.content_object = self.content_object
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Файл прикреплён.')
        return super().form_valid(form)

    def get_success_url(self):
        if self.task_pk:
            return reverse('qa_app:task_detail', kwargs={'pk': self.task_pk})
        elif self.content_object and hasattr(self.content_object, 'task'):
            return reverse('qa_app:task_detail', kwargs={'pk': self.content_object.task.pk})
        else:
            # Надёжный fallback
            return reverse('qa_app:task_list')
