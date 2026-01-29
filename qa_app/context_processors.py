from django.db.models import Count, Q
from .models import Category, Question
import re


def categories_context(request):
    """Добавляет список категорий в контекст всех шаблонов"""
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