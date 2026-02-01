from django.core.cache import cache
from django.db.models import Q, Count
from .models import Category, Question, Tag

def sidebar_context(request):
    cache_key = 'sidebar_context'
    context = cache.get(cache_key)
    if context is None:
        categories = Category.objects.annotate(
            question_count=Count('question', filter=Q(question__is_published=True))
        ).order_by('name')

        total_questions = Question.objects.filter(is_published=True).count()
        answered_count = Question.objects.filter(is_published=True).exclude(answer='').count()
        unanswered_count = total_questions - answered_count

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

        context = {
            'sidebar_categories': categories,
            'sidebar_question_count': total_questions,
            'sidebar_answered_count': answered_count,
            'sidebar_unanswered_count': unanswered_count,
            'sidebar_popular_tags': popular_tags,
        }
        cache.set(cache_key, context, 60 * 15)  # Кэш на 15 минут
    return context