from django.contrib import admin
from .models import Question, Category, QuestionFile, AnswerFile


class QuestionFileInline(admin.TabularInline):
    model = QuestionFile
    extra = 1


class AnswerFileInline(admin.TabularInline):
    model = AnswerFile
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at', 'is_published', 'has_answer')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'content', 'answer', 'tags')
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at', 'views')
    inlines = [QuestionFileInline, AnswerFileInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'category', 'tags')
        }),
        ('Ответ', {
            'fields': ('answer',),
            'classes': ('wide',)
        }),
        ('Метаданные', {
            'fields': ('author', 'is_published', 'views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuestionFile)
class QuestionFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'question', 'uploaded_at', 'get_file_size')
    list_filter = ('uploaded_at',)
    search_fields = ('name', 'question__title')
    readonly_fields = ('uploaded_at',)


@admin.register(AnswerFile)
class AnswerFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'question', 'uploaded_by', 'uploaded_at', 'get_file_size')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('name', 'question__title')
    readonly_fields = ('uploaded_at',)