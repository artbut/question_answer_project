from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType

register = template.Library()

@register.filter
def striptags(value):
    """
    Удаляет HTML-теги из строки.
    Аналог strip_tags, но как шаблонный фильтр.
    """
    return strip_tags(value)

@register.filter
def truncatewords_html(value, num):
    """
    Обрезает HTML-содержимое до N слов, сохраняя структуру.
    """
    from django.utils.text import Truncator
    return Truncator(value).words(num, html=True)


@register.filter
def filter_by_content_object(queryset, obj):
    """Фильтрует AttachedFile по content_object"""
    ct = ContentType.objects.get_for_model(obj)
    return queryset.filter(content_type=ct, object_id=obj.pk)


@register.filter
def can_delete_file(file_obj, user):
    """
    Проверяет, может ли пользователь удалить файл.
    """
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    if hasattr(file_obj, 'question') and file_obj.question and file_obj.question.author == user:
        return True
    if hasattr(file_obj, 'uploaded_by') and file_obj.uploaded_by == user:
        return True
    return False