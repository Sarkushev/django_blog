from django.db import models


class Blog(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    content = models.TextField("Текст статьи")
    created_at = models.DateTimeField(auto_now_add=True)

    # Задание 2: счётчик лайков/просмотров, по умолчанию 0
    likes = models.PositiveIntegerField("Лайки", default=0)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title
