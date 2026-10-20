from django.db.models import F
from django.views.generic import DetailView, ListView

from .models import Blog


class BlogListView(ListView):
    model = Blog
    template_name = "blog/blog_list.html"
    context_object_name = "blogs"


class BlogDetailView(DetailView):
    model = Blog
    template_name = "blog/blog_detail.html"
    context_object_name = "blog"

    def get_object(self, queryset=None):
        # Если блога нет, super() бросит Http404, и счётчик не тронется
        blog = super().get_object(queryset)

        # --- ЛОГИКА ЛАЙКОВ (Задание 2). Для шага "тест падает" закомментируй 3 строки ниже ---
        Blog.objects.filter(pk=blog.pk).update(likes=F("likes") + 1)
        blog.refresh_from_db()
        # --- конец логики лайков ---

        return blog
