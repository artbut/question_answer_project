from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Category, Question, Tag, AttachedFile


# ----------------------------
# Вложенные файлы через GenericForeignKey
# ----------------------------

class AttachedFileInline(GenericTabularInline):
    """
    Инлайн для прикреплённых файлов.
    Использует GenericForeignKey, чтобы работать с любыми моделями.
    """
    model = AttachedFile
    extra = 0
    readonly_fields = ('uploaded_at', 'get_file_size')
    fields = ('file', 'name', 'uploaded_by', 'uploaded_at', 'get_file_size')

    def get_file_size(self, obj):
        return obj.get_file_size()
    get_file_size.short_description = "Размер файла"


# ----------------------------
# Админка: Категория
# ----------------------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'question_count', 'description_preview')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    list_per_page = 20

    def question_count(self, obj):
        return obj.question_set.filter(is_published=True).count()
    question_count.short_description = "Кол-во вопросов"

    def description_preview(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_preview.short_description = "Описание"


# ----------------------------
# Админка: Тег
# ----------------------------

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'usage_count')
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 20

    def usage_count(self, obj):
        # Предварительно добавьте related_name или используйте get_queryset в нужных местах
        try:
            # Это пример — в реальности может потребовать кастомной логики
            content_type = obj.content_type.model_class()
            return obj.object_id
        except:
            pass
        return "—"
    usage_count.short_description = "Использовано раз"


# ----------------------------
# Админка: Вопрос
# ----------------------------

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'author', 'created_at',
        'is_published', 'has_answer', 'views'
    )
    list_filter = (
        'is_published', 'category', 'created_at', 'tags',
        'author'
    )
    search_fields = ('title', 'content', 'answer', 'tags__name', 'author__username')
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at', 'views')
    filter_horizontal = ('tags',)
    inlines = [AttachedFileInline]
    ordering = ('-created_at',)
    list_per_page = 15
    date_hierarchy = 'created_at'
    save_as = True

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'category', 'tags')
        }),
        ('Ответ', {
            'fields': ('answer',),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('author', 'is_published', 'views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_answer(self, obj):
        return bool(obj.answer.strip())
    has_answer.boolean = True
    has_answer.short_description = "Есть ответ"


# ----------------------------
# Админка: Прикреплённые файлы (отдельно)
# ----------------------------

@admin.register(AttachedFile)
class AttachedFileAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'linked_object', 'content_type',
        'uploaded_by', 'uploaded_at', 'get_file_size'
    )
    list_filter = ('content_type', 'uploaded_at', 'uploaded_by')
    search_fields = ('name', 'object_id')
    readonly_fields = ('uploaded_at', 'get_file_size')
    raw_id_fields = ('uploaded_by',)
    list_per_page = 20

    def linked_object(self, obj):
        """Показывает ссылку на связанный объект"""
        if obj.content_object:
            url = f"/admin/{obj.content_type.app_label}/{obj.content_type.model}/{obj.object_id}/change/"
            return f'<a href="{url}">{obj.content_object}</a>'
        return "—"
    linked_object.allow_tags = True
    linked_object.short_description = "Связанный объект"

    def get_file_size(self, obj):
        return obj.get_file_size()
    get_file_size.short_description = "Размер файла"