from django.db.models import F
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import BlogForm
from .models import Blog


# ----------------------------- R (Read) -----------------------------

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


# ----------------------------- C (Create) ---------------------------

class BlogCreateView(CreateView):
    model = Blog
    form_class = BlogForm
    template_name = "blog/blog_form.html"
    success_url = reverse_lazy("blog:list")


# ----------------------------- U (Update) ---------------------------

class BlogUpdateView(UpdateView):
    model = Blog
    form_class = BlogForm
    template_name = "blog/blog_form.html"
    context_object_name = "blog"
    success_url = reverse_lazy("blog:list")


# ----------------------------- D (Delete) ---------------------------

class BlogDeleteView(DeleteView):
    model = Blog
    template_name = "blog/blog_confirm_delete.html"
    context_object_name = "blog"
    success_url = reverse_lazy("blog:list")
