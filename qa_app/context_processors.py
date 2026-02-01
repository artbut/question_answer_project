from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q, Count
from .models import Category, Question, Tag, Task, SearchQuery


def sidebar_context(request):
    cache_key = 'sidebar_context'
    context = cache.get(cache_key)
    if context is None:
        # Категории с количеством опубликованных вопросов
        categories = Category.objects.annotate(
            question_count=Count('question', filter=Q(question__is_published=True))
        ).order_by('name')

        # Статистика по вопросам
        total_questions = Question.objects.filter(is_published=True).count()
        answered_count = Question.objects.filter(is_published=True).exclude(answer='').count()
        unanswered_count = total_questions - answered_count

        # Популярные поисковые запросы за последние 30 дней
        popular_searches = SearchQuery.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).values('term').annotate(
            count=Count('term')
        ).order_by('-count')[:10]

        # Популярные теги (из вопросов)
        questions_with_tags = Question.objects.filter(
            is_published=True
        ).prefetch_related('tags')

        tag_counts = {}
        for question in questions_with_tags:
            for tag in question.tags.all():
                tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1

        popular_tags = sorted(
            [{'name': tag, 'count': count} for tag, count in tag_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]

        # Новая статистика: количество задач и последние задачи
        total_tasks = Task.objects.count()
        recent_tasks = Task.objects.select_related('author') \
            .order_by('-created_at')[:5]

        # Объединённый контекст
        context = {
            'sidebar_categories': categories,
            'sidebar_question_count': total_questions,
            'sidebar_answered_count': answered_count,
            'sidebar_unanswered_count': unanswered_count,
            'sidebar_popular_tags': popular_tags,
            'sidebar_total_tasks': total_tasks,
            'sidebar_recent_tasks': recent_tasks,
            'popular_searches': popular_searches,  # Добавлено: популярные поисковые запросы
        }
        cache.set(cache_key, context, 60 * 15)  # Кэш на 15 минут
    return context