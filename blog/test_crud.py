"""Тесты CRUD-операций приложения blog.

C (Create) — BlogCreateTests
R (Read)   — тесты List/Detail лежат в blog/tests.py; здесь только проверка,
             что созданная статья читается (в классе BlogCrudFlowTests)
U (Update) — BlogUpdateTests
D (Delete) — BlogDeleteTests
Полный цикл C -> R -> U -> D — BlogCrudFlowTests

Запуск:  python manage.py test blog -v 2
"""
from django.test import Client, TestCase
from django.urls import reverse

from .models import Blog


class CrudTestBase(TestCase):
    """Общая подготовка: две статьи в тестовой базе."""

    def setUp(self):
        self.blog1 = Blog.objects.create(title="Первая статья", content="Текст первой статьи")
        self.blog2 = Blog.objects.create(title="Вторая статья", content="Текст второй статьи")

    @staticmethod
    def valid_data(**overrides):
        data = {"title": "Новая статья", "content": "Текст новой статьи"}
        data.update(overrides)
        return data


# =====================================================================
# C — CREATE
# =====================================================================

class BlogCreateTests(CrudTestBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("blog:create")

    # --- страница с формой (GET) ---

    def test_create_page_returns_200_and_uses_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/blog_form.html")

    def test_create_page_contains_form_fields_and_csrf_token(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="content"')
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_list_has_link_to_create_page(self):
        response = self.client.get(reverse("blog:list"))
        self.assertContains(response, f'href="{self.url}"')

    # --- успешное создание (POST) ---

    def test_create_with_valid_data_creates_blog(self):
        before = Blog.objects.count()
        self.client.post(self.url, self.valid_data())
        self.assertEqual(Blog.objects.count(), before + 1)
        blog = Blog.objects.get(title="Новая статья")
        self.assertEqual(blog.content, "Текст новой статьи")

    def test_create_redirects_to_list(self):
        response = self.client.post(self.url, self.valid_data())
        self.assertRedirects(response, reverse("blog:list"))

    def test_created_blog_has_zero_likes(self):
        self.client.post(self.url, self.valid_data())
        self.assertEqual(Blog.objects.get(title="Новая статья").likes, 0)

    def test_create_ignores_likes_sent_in_post(self):
        self.client.post(self.url, self.valid_data(likes=100))
        self.assertEqual(Blog.objects.get(title="Новая статья").likes, 0)

    def test_created_blog_appears_in_list(self):
        self.client.post(self.url, self.valid_data(title="Статья из теста"))
        response = self.client.get(reverse("blog:list"))
        self.assertContains(response, "Статья из теста")

    # --- невалидные данные ---

    def test_create_with_empty_title_shows_error_and_creates_nothing(self):
        before = Blog.objects.count()
        response = self.client.post(self.url, self.valid_data(title=""))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("title", code="required"))
        self.assertEqual(Blog.objects.count(), before)

    def test_create_with_empty_content_shows_error_and_creates_nothing(self):
        before = Blog.objects.count()
        response = self.client.post(self.url, self.valid_data(content=""))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("content", code="required"))
        self.assertEqual(Blog.objects.count(), before)

    def test_create_with_whitespace_only_title_is_rejected(self):
        before = Blog.objects.count()
        response = self.client.post(self.url, self.valid_data(title="   "))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("title", code="required"))
        self.assertEqual(Blog.objects.count(), before)

    def test_create_title_length_boundaries(self):
        # граничные значения max_length=200: 1 и 200 допустимы, 201 — нет
        for length, is_valid in ((1, True), (200, True), (201, False)):
            with self.subTest(title_length=length):
                before = Blog.objects.count()
                response = self.client.post(self.url, self.valid_data(title="а" * length))
                if is_valid:
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(Blog.objects.count(), before + 1)
                else:
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context["form"].has_error("title", code="max_length"))
                    self.assertEqual(Blog.objects.count(), before)

    def test_create_without_csrf_token_is_forbidden(self):
        strict_client = Client(enforce_csrf_checks=True)
        before = Blog.objects.count()
        response = strict_client.post(self.url, self.valid_data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Blog.objects.count(), before)


# =====================================================================
# U — UPDATE
# =====================================================================

class BlogUpdateTests(CrudTestBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("blog:update", args=[self.blog1.pk])

    # --- страница редактирования (GET) ---

    def test_update_page_returns_200_and_uses_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/blog_form.html")

    def test_update_page_is_prefilled_with_current_values(self):
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertEqual(form.initial["title"], "Первая статья")
        self.assertEqual(form.initial["content"], "Текст первой статьи")

    def test_update_page_for_nonexistent_id_returns_404(self):
        response = self.client.get(reverse("blog:update", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_open_update_page_does_not_change_likes(self):
        self.client.get(self.url)
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.likes, 0)

    def test_detail_has_links_to_edit_and_delete(self):
        response = self.client.get(reverse("blog:detail", args=[self.blog1.pk]))
        self.assertContains(response, f'href="{self.url}"')
        self.assertContains(response, f'href="{reverse("blog:delete", args=[self.blog1.pk])}"')

    # --- успешное изменение (POST) ---

    def test_update_with_valid_data_changes_title_and_content(self):
        self.client.post(self.url, self.valid_data(title="Изменённый заголовок", content="Изменённый текст"))
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.title, "Изменённый заголовок")
        self.assertEqual(self.blog1.content, "Изменённый текст")

    def test_update_redirects_to_list(self):
        response = self.client.post(self.url, self.valid_data())
        self.assertRedirects(response, reverse("blog:list"))

    def test_update_does_not_create_new_blog(self):
        before = Blog.objects.count()
        self.client.post(self.url, self.valid_data())
        self.assertEqual(Blog.objects.count(), before)

    def test_update_keeps_likes(self):
        Blog.objects.filter(pk=self.blog1.pk).update(likes=5)
        self.client.post(self.url, self.valid_data())
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.likes, 5)

    def test_update_ignores_likes_sent_in_post(self):
        self.client.post(self.url, self.valid_data(likes=999))
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.likes, 0)

    def test_update_changes_only_this_blog(self):
        self.client.post(self.url, self.valid_data(title="Изменено"))
        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.title, "Вторая статья")
        self.assertEqual(self.blog2.content, "Текст второй статьи")

    # --- невалидные данные и ошибки ---

    def test_update_with_empty_title_shows_error_and_keeps_old_data(self):
        response = self.client.post(self.url, self.valid_data(title=""))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("title", code="required"))
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.title, "Первая статья")

    def test_update_with_too_long_title_is_rejected(self):
        response = self.client.post(self.url, self.valid_data(title="а" * 201))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("title", code="max_length"))
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.title, "Первая статья")

    def test_update_post_for_nonexistent_id_returns_404(self):
        response = self.client.post(reverse("blog:update", args=[999999]), self.valid_data())
        self.assertEqual(response.status_code, 404)

    def test_update_without_csrf_token_is_forbidden(self):
        strict_client = Client(enforce_csrf_checks=True)
        response = strict_client.post(self.url, self.valid_data(title="Взлом"))
        self.assertEqual(response.status_code, 403)
        self.blog1.refresh_from_db()
        self.assertEqual(self.blog1.title, "Первая статья")


# =====================================================================
# D — DELETE
# =====================================================================

class BlogDeleteTests(CrudTestBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("blog:delete", args=[self.blog1.pk])

    # --- страница подтверждения (GET) ---

    def test_delete_page_returns_200_and_shows_confirmation(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/blog_confirm_delete.html")
        self.assertContains(response, "Первая статья")

    def test_get_does_not_delete_blog(self):
        self.client.get(self.url)
        self.assertTrue(Blog.objects.filter(pk=self.blog1.pk).exists())

    # --- успешное удаление (POST) ---

    def test_post_deletes_blog(self):
        before = Blog.objects.count()
        self.client.post(self.url)
        self.assertEqual(Blog.objects.count(), before - 1)
        self.assertFalse(Blog.objects.filter(pk=self.blog1.pk).exists())

    def test_delete_redirects_to_list(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("blog:list"))

    def test_delete_removes_only_this_blog(self):
        self.client.post(self.url)
        self.assertTrue(Blog.objects.filter(pk=self.blog2.pk).exists())

    def test_deleted_blog_detail_returns_404(self):
        self.client.post(self.url)
        response = self.client.get(reverse("blog:detail", args=[self.blog1.pk]))
        self.assertEqual(response.status_code, 404)

    def test_deleted_blog_disappears_from_list(self):
        self.client.post(self.url)
        response = self.client.get(reverse("blog:list"))
        self.assertNotContains(response, "Первая статья")
        self.assertContains(response, "Вторая статья")

    # --- ошибки ---

    def test_delete_page_for_nonexistent_id_returns_404(self):
        response = self.client.get(reverse("blog:delete", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_post_for_nonexistent_id_returns_404(self):
        response = self.client.post(reverse("blog:delete", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_repeated_delete_returns_404(self):
        self.client.post(self.url)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_delete_without_csrf_token_is_forbidden(self):
        strict_client = Client(enforce_csrf_checks=True)
        response = strict_client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Blog.objects.filter(pk=self.blog1.pk).exists())


# =====================================================================
# Полный цикл C -> R -> U -> D
# =====================================================================

class BlogCrudFlowTests(CrudTestBase):

    def test_full_crud_cycle(self):
        # Create
        self.client.post(reverse("blog:create"), {"title": "Цикл", "content": "Текст цикла"})
        blog = Blog.objects.get(title="Цикл")

        # Read
        self.assertContains(self.client.get(reverse("blog:list")), "Цикл")
        detail = self.client.get(reverse("blog:detail", args=[blog.pk]))
        self.assertContains(detail, "Текст цикла")

        # Update
        self.client.post(
            reverse("blog:update", args=[blog.pk]),
            {"title": "Цикл (изменён)", "content": "Новый текст цикла"},
        )
        blog.refresh_from_db()
        self.assertEqual(blog.title, "Цикл (изменён)")
        self.assertEqual(blog.content, "Новый текст цикла")

        # Delete
        self.client.post(reverse("blog:delete", args=[blog.pk]))
        self.assertFalse(Blog.objects.filter(pk=blog.pk).exists())
        self.assertEqual(self.client.get(reverse("blog:detail", args=[blog.pk])).status_code, 404)
