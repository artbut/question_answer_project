from django import template
from django.db.models import Count
from django.db.models.functions import Length
from qa_app.models import Question, Category
import re

register = template.Library()


@register.simple_tag
def total_questions():
    """Возвращает общее количество вопросов"""
    return Question.objects.filter(is_published=True).count()


@register.simple_tag
def answered_questions_count():
    """Возвращает количество вопросов с ответами"""
    return Question.objects.filter(is_published=True).exclude(answer='').count()


@register.simple_tag
def unanswered_questions_count():
    """Возвращает количество вопросов без ответов"""
    return Question.objects.filter(is_published=True, answer='').count()


@register.simple_tag
def get_popular_tags(limit=10):
    """Возвращает популярные теги"""
    questions = Question.objects.filter(is_published=True, tags__isnull=False).exclude(tags='')

    tag_counts = {}
    for question in questions:
        tags = [tag.strip() for tag in question.tags.split(',') if tag.strip()]
        for tag in tags:
            if tag in tag_counts:
                tag_counts[tag] += 1
            else:
                tag_counts[tag] = 1

    # Сортируем по количеству и ограничиваем
    popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    # Преобразуем в список словарей для удобства
    result = []
    for tag, count in popular_tags:
        result.append({
            'name': tag,
            'count': count,
            'slug': re.sub(r'[^\w\s-]', '', tag).strip().lower().replace(' ', '-')
        })

    return result


@register.filter
def get_category_stats(category):
    """Получает статистику по категории"""
    total = category.question_set.filter(is_published=True).count()
    answered = category.question_set.filter(is_published=True).exclude(answer='').count()

    return {
        'total': total,
        'answered': answered,
        'unanswered': total - answered,
        'percentage': (answered / total * 100) if total > 0 else 0
    }