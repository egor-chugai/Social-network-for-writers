from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User
from http import HTTPStatus


class PostURLTests(TestCase):
    GROUP_TITLE: str = 'test_group'
    GROUP_SLUG: str = 'test_slug'
    GROUP_DESCRIPTION: str = 'test_description'
    POST_TEXT: str = 'test_post'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title=cls.GROUP_TITLE,
            slug=cls.GROUP_SLUG,
            description=cls.GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=cls.POST_TEXT,
            group=cls.group
        )
        cls.public_pages = {
            "/": "posts/index.html",
            "/group/test_slug/": "posts/group_list.html",
            f"/profile/{cls.user}/": "posts/profile.html",
            f"/posts/{cls.post.pk}/": "posts/post_detail.html",
        }
        cls.private_pages = {
            "/create/": "posts/create_post.html",
            f"/posts/{cls.post.pk}/edit/": "posts/create_post.html",
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.not_author_authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.not_author_authorized_client.force_login(self.user)

    def test_public_pages_exists_at_desired_locations(self):
        """Публичные страницы доступны любому пользователю."""
        for page in self.public_pages:
            with self.subTest(address=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_correct_guest_redirect_from_private_pages(self):
        """Неавторизованный пользователь корректно переадресуется
        на страницу авторизации
        """
        response = self.guest_client.get("/create/")
        self.assertRedirects(response,
                             reverse('users:login')
                             + '?next='
                             + reverse('posts:create_post'))
        response = self.guest_client.get(f"/posts/{self.post.pk}/edit/")
        self.assertRedirects(response,
                             reverse('users:login')
                             + '?next='
                             + f'/posts/{self.post.pk}/edit/')

    def test_private_pages_exists_at_desired_locations(self):
        """Приватные страницы доступны авторизованному пользователю."""
        for page in self.private_pages:
            with self.subTest(address=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_pages_uses_correct_template(self):
        """Публичные URL-адреса используют соответствующие шаблоны."""
        for page, template in self.public_pages.items():
            with self.subTest(address=page):
                response = self.guest_client.get(page)
                self.assertTemplateUsed(response, template)

    def test_private_pages_uses_correct_template(self):
        """приватные URL-адреса используют соответствующие шаблоны."""
        for page, template in self.private_pages.items():
            with self.subTest(address=page):
                response = self.authorized_client.get(page)
                self.assertTemplateUsed(response, template)

    def test_post_edit_by_not_author(self):
        """Перенапрявляет на страницу поста при
        попытке редактирования не автором
        """
        response = self.not_author_authorized_client.get(
            f"/posts/{self.post.pk}/edit/"
        )
        self.assertRedirects(
            response, f'/posts/{self.post.pk}/'
        )

    def test_unexisting_page_return_404(self):
        """Переход на /unexisting_page/ вернет ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexisting_page_use_correct_template(self):
        """Переход на /unexisting_page/ вернет ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, "core/404.html")
