from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
from .models import AttachedFile


@receiver(post_delete, sender=AttachedFile)
def delete_file_on_delete(sender, instance, **kwargs):
    print(f"🔧 Сигнал post_delete вызван для файла: {instance.id}")
    if instance.file:
        file_path = instance.file.path
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Файл удалён с диска: {file_path}")
            except OSError as e:
                print(f"❌ Ошибка при удалении файла {file_path}: {e}")
        else:
            print(f"⚠️ Файл не существует на диске: {file_path}")
    else:
        print("⚠️ У объекта нет файла для удаления")