from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, User


class CacheTests(TestCase):
    POST_TEXT: str = 'test_post'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.post = Post.objects.create(
            author=cls.author,
            text=cls.POST_TEXT
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_cache_index_page(self):
        """Кеширование на главной странице работает нормально"""
        post_before = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.post.delete()
        post_after = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(post_before, post_after)
        cache.clear()
        cache_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(post_before, cache_content)
