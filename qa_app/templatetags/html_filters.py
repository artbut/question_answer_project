from django import template
from django.utils.html import strip_tags
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def striptags(value):
    """
    Удаляет HTML-теги из строки.
    """
    if not value:
        return ''
    return strip_tags(value)


@register.filter
def truncatewords_html(value, num):
    """
    Обрезает HTML-содержимое до N слов, сохраняя структуру тегов.
    """
    from django.utils.text import Truncator
    if not value:
        return ''
    return Truncator(value).words(num, html=True)


@register.filter
def filter_by_content_object(queryset, obj):
    """
    Фильтрует AttachedFile по связанному объекту (вопрос, задача, запись).
    Использует GenericForeignKey.
    """
    if not obj or not obj.pk:
        return queryset.none()
    ct = ContentType.objects.get_for_model(obj)
    return queryset.filter(content_type=ct, object_id=obj.pk)


@register.filter
def can_delete_file(file_obj, user):
    """
    Проверяет, может ли пользователь удалить файл.
    Права:
    - Суперпользователь / staff — да
    - Загрузивший пользователь — да
    - Автор связанного объекта (если у него есть author) — да
    Работает с Question, Task, TaskNote.
    """
    if not user.is_authenticated:
        return False

    # Сотрудник всегда может
    if user.is_staff:
        return True

    # Пользователь, который загрузил файл
    if hasattr(file_obj, 'uploaded_by') and file_obj.uploaded_by == user:
        return True

    # Автор связанного объекта
    content_object = getattr(file_obj, 'content_object', None)
    if content_object and hasattr(content_object, 'author') and content_object.author == user:
        return True

    return False


@register.filter
def get_content_type(obj):
    """
    Возвращает тип контента для объекта (например, 'question', 'task').
    Полезно для шаблонов при работе с GenericForeignKey.
    """
    if not obj:
        return ''
    return obj._meta.model_name


@register.filter
def get_verbose_name(obj):
    """
    Возвращает человекочитаемое название модели.
    """
    if not obj:
        return ''
    return obj._meta.verbose_name.capitalize()


@register.filter
def has_notes(task):
    """
    Проверяет, есть ли у задачи записи.
    """
    return task.notes.exists() if hasattr(task, 'notes') else False


@register.filter
def get_files_count(obj):
    """
    Возвращает количество прикреплённых файлов к объекту.
    Использует GenericRelation для прямого доступа.
    """
    if not obj or not obj.pk:
        return 0
    try:
        # Пробуем использовать GenericRelation (настоящий способ)
        if hasattr(obj, 'attachedfile_set'):
            return obj.attachedfile_set.count()

        # Резервный способ: через ContentType (если нет GenericRelation)
        ct = ContentType.objects.get_for_model(obj)
        return ct.attachedfile_set.filter(object_id=obj.pk).count()
    except Exception:
        return 0


@register.filter
def order_by_order(queryset):
    """
    Сортирует queryset по полю 'order'.
    Для использования с TaskNote.
    """
    return queryset.order_by('order')


@register.filter
def highlight_search(text, query):
    """
    Подсвечивает поисковый запрос в тексте.
    """
    if not query or not text:
        return text
    # Экранируем спецсимволы в запросе
    escaped_query = re.escape(query.strip())
    # Ищем с учётом регистра, оборачиваем в <mark>
    regex = re.compile(f'({escaped_query})', re.IGNORECASE)
    highlighted = regex.sub(r'<mark class="highlight">\1</mark>', text)
    return mark_safe(highlighted)