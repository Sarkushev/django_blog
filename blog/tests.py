from django.test import TestCase
from django.urls import reverse

from .models import Blog


class BlogTestBase(TestCase):
    """Общая подготовка: три блога в тестовой базе."""

    def setUp(self):
        self.blog1 = Blog.objects.create(title="Первая статья", content="Текст первой статьи")
        self.blog2 = Blog.objects.create(title="Вторая статья", content="Текст второй статьи")
        self.blog3 = Blog.objects.create(title="Третья статья", content="Текст третьей статьи")


# =====================================================================
# ЗАДАНИЕ 1. Тесты List и Detail (разные варианты получения данных)
# =====================================================================

class BlogListTests(BlogTestBase):

    def test_list_returns_200_and_uses_template(self):
        response = self.client.get(reverse("blog:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/blog_list.html")

    def test_list_contains_all_blog_titles(self):
        response = self.client.get(reverse("blog:list"))
        for blog in (self.blog1, self.blog2, self.blog3):
            self.assertContains(response, blog.title)

    def test_list_context_has_all_blogs(self):
        response = self.client.get(reverse("blog:list"))
        self.assertEqual(len(response.context["blogs"]), 3)

    def test_empty_list_shows_message_instead_of_content(self):
        Blog.objects.all().delete()
        response = self.client.get(reverse("blog:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пока нет статей")
        self.assertEqual(len(response.context["blogs"]), 0)

    def test_list_links_lead_to_detail_pages(self):
        response = self.client.get(reverse("blog:list"))
        for blog in (self.blog1, self.blog2, self.blog3):
            url = reverse("blog:detail", args=[blog.pk])
            self.assertContains(response, f'href="{url}"')      # ссылка есть
            detail = self.client.get(url)                        # и по ней можно перейти
            self.assertEqual(detail.status_code, 200)
            self.assertContains(detail, blog.title)


class BlogDetailTests(BlogTestBase):

    def test_detail_returns_200_and_uses_template(self):
        response = self.client.get(reverse("blog:detail", args=[self.blog1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/blog_detail.html")

    def test_detail_contains_title_and_content(self):
        response = self.client.get(reverse("blog:detail", args=[self.blog1.pk]))
        self.assertContains(response, "Первая статья")
        self.assertContains(response, "Текст первой статьи")

    def test_detail_returns_correct_blog_by_id(self):
        response = self.client.get(reverse("blog:detail", args=[self.blog2.pk]))
        self.assertEqual(response.context["blog"].pk, self.blog2.pk)
        self.assertContains(response, f"ID: {self.blog2.pk}")
        self.assertNotContains(response, "Текст первой статьи")  # чужой контент не попал

    def test_detail_for_nonexistent_id_returns_404(self):
        response = self.client.get(reverse("blog:detail", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_detail_for_invalid_ids_returns_404(self):
        base = reverse("blog:list")
        for bad in ("abc", "-1", "1.5", "0"):
            with self.subTest(bad_id=bad):
                response = self.client.get(f"{base}{bad}/")
                self.assertEqual(response.status_code, 404)

    def test_detail_has_working_link_back_to_list(self):
        response = self.client.get(reverse("blog:detail", args=[self.blog1.pk]))
        list_url = reverse("blog:list")
        self.assertContains(response, f'href="{list_url}"')
        self.assertEqual(self.client.get(list_url).status_code, 200)

    def test_detail_rejects_post_method(self):
        response = self.client.post(reverse("blog:detail", args=[self.blog1.pk]))
        self.assertEqual(response.status_code, 405)


# =====================================================================
# ЗАДАНИЕ 2. Счётчик лайков/просмотров
# =====================================================================

class BlogLikesTests(BlogTestBase):

    def test_new_blog_has_zero_likes(self):
        blog = Blog.objects.create(title="Новый", content="Текст")
        self.assertEqual(blog.likes, 0)

    def test_detail_get_increases_likes_to_one(self):
        url = reverse("blog:detail", args=[self.blog1.pk])
        self.client.get(url)
        self.blog1.refresh_from_db()          # перечитываем данные из БД
        self.assertEqual(self.blog1.likes, 1)

    # --- дополнительные проверки ---

    def test_each_visit_adds_one(self):
        url = reverse("blog:detail", args=[self.blog1.pk])
        for _ in range(3):
            self.client.get(url)
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.likes, 3)

    def test_visit_changes_only_this_blog(self):
        self.client.get(reverse("blog:detail", args=[self.blog1.pk]))
        self.blog2.refresh_from_db()
        self.blog3.refresh_from_db()
        self.assertEqual(self.blog2.likes, 0)
        self.assertEqual(self.blog3.likes, 0)

    def test_list_page_does_not_change_likes(self):
        self.client.get(reverse("blog:list"))
        for blog in (self.blog1, self.blog2, self.blog3):
            blog.refresh_from_db()
            self.assertEqual(blog.likes, 0)

    def test_404_does_not_change_any_likes(self):
        self.client.get(reverse("blog:detail", args=[999999]))
        for blog in (self.blog1, self.blog2, self.blog3):
            blog.refresh_from_db()
            self.assertEqual(blog.likes, 0)

    def test_page_shows_updated_likes(self):
        response = self.client.get(reverse("blog:detail", args=[self.blog1.pk]))
        self.assertContains(response, "Лайки: 1")
