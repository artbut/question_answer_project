from django.apps import AppConfig


class QaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'qa_app'

    def ready(self):
        try:
            import qa_app.signals
            print("✅ Сигналы загружены: qa_app.signals")
        except Exception as e:
            print(f"❌ Ошибка при загрузке сигналов: {e}")
