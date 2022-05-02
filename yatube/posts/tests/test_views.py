from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group, User, Follow

NUMBER_OF_POSTS: int = 13
NUMBER_OF_POSTS_FIRST_PAGE: int = 10
NUMBER_OF_POSTS_SECOND_PAGE: int = 3
GROUP_TITLE: str = 'test_group'
GROUP_SLUG: str = 'test_slug'
GROUP_DESCRIPTION: str = 'test_description'
POST_TEXT: str = 'test_post'
LAST_POST_TEXT: str = 'test_post_13'
POST_IMAGE: str = 'posts/small.gif'


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        for post in range(NUMBER_OF_POSTS):
            cls.post = Post.objects.create(
                author=cls.author,
                text=f'{POST_TEXT}_{post + 1}',
                group=cls.group,
                image='posts/small.gif'
            )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.author}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.image, POST_IMAGE)
        self.assertEqual(first_object.text, LAST_POST_TEXT)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context.get('group').title, GROUP_TITLE)
        self.assertEqual(response.context.get('group').slug, GROUP_SLUG)
        self.assertEqual(
            response.context.get('group').description, GROUP_DESCRIPTION
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.image, POST_IMAGE)
        self.assertEqual(first_object.text, LAST_POST_TEXT)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author})
        )
        self.assertEqual(response.context.get('author').username, 'Author')
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.image, POST_IMAGE)
        self.assertEqual(first_object.text, LAST_POST_TEXT)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(
            response.context.get('post').text, LAST_POST_TEXT
        )
        post = response.context['post']
        self.assertEqual(post.image, POST_IMAGE)
        self.assertEqual(post.text, LAST_POST_TEXT)

    def test_post_create_page_show_correct_context(self):
        """Контекст страницы создания поста
        содержит корректную форму."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected_type in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, expected_type)

    def test_post_edit_page_show_correct_post_context(self):
        """Контекст страницы редактирования поста
        содержит корректный пост."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        context = response.context['post']
        expect_post = PostPagesTests.post
        self.assertEqual(context, expect_post)

    def test_index_first_page_contains_ten_records(self):
        """Паджинатор отображает нужное к-во постов на первой странице
        в index, group_list, profile."""
        response_index = self.client.get(reverse('posts:index'))
        response_group_list = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        response_profile = self.client.get(
            reverse('posts:profile', kwargs={'username': self.author})
        )
        self.assertEqual(len(response_index.context['page_obj']),
                         NUMBER_OF_POSTS_FIRST_PAGE)
        self.assertEqual(len(response_group_list.context['page_obj']),
                         NUMBER_OF_POSTS_FIRST_PAGE)
        self.assertEqual(len(response_profile.context['page_obj']),
                         NUMBER_OF_POSTS_FIRST_PAGE)

    def test_index_second_page_contains_three_records(self):
        """Паджинатор отображает нужное к-во постов на второй странице
        в index, group_list, profile."""
        response_index = self.client.get(reverse('posts:index') + '?page=2')
        response_group_list = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2')
        response_profile = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': self.author}) + '?page=2')
        self.assertEqual(len(response_index.context['page_obj']),
                         NUMBER_OF_POSTS_SECOND_PAGE)
        self.assertEqual(len(response_group_list.context['page_obj']),
                         NUMBER_OF_POSTS_SECOND_PAGE)
        self.assertEqual(len(response_profile.context['page_obj']),
                         NUMBER_OF_POSTS_SECOND_PAGE)


class FollowTests(TestCase):
    NUMBER_OF_POSTS_FOR_SUBSCRUBERS: int = 1
    NUMBER_OF_POSTS_FOR_UNSUBSCRUBERS: int = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            author=cls.author,
            text=POST_TEXT
        )
        cls.followers_number = Follow.objects.count()

    def setUp(self):
        self.subscribed_user = Client()
        self.subscribed_user.force_login(self.user)
        self.unsubscribed_user = Client()
        self.unsubscribed_user.force_login(self.user_2)

    def test_authorized_user_can_follow_other_users(self):
        """Авторизованный пользователь может подписываться
        на других пользователей
        """
        follow = self.subscribed_user.post(
            reverse('posts:profile_follow', args=[self.author])
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )
        self.assertEqual(
            Follow.objects.count(), self.followers_number + 1
        )
        self.assertRedirects(
            follow, reverse(
                'posts:profile', args=[self.author]
            )
        )

    def test_subscribed_user_can_see_author_posts(self):
        """Новая запись пользователя появляется
        в ленте тех, кто на него подписан
        """
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.subscribed_user.get(
            reverse('posts:follow_index')
        ).context['page_obj']
        self.assertEqual(
            self.NUMBER_OF_POSTS_FOR_SUBSCRUBERS, len(response)
        )
        response = self.unsubscribed_user.get(
            reverse('posts:follow_index')
        ).context['page_obj']
        self.assertEqual(
            self.NUMBER_OF_POSTS_FOR_UNSUBSCRUBERS, len(response)
        )

    def test_authorized_user_can_unfollow_other_users(self):
        """Авторизованный пользователь может отписываться
        от других пользователей
        """
        Follow.objects.filter(
            user=self.user,
            author=self.author
        ).delete()
        self.assertEqual(
            Follow.objects.count(), self.followers_number
        )
