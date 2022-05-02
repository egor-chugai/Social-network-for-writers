import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..forms import PostForm, CommentForm
from ..models import Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    GROUP_TITLE: str = 'test_group'
    GROUP_SLUG: str = 'test_slug'
    GROUP_DESCRIPTION: str = 'test_description'
    POST_TEXT: str = 'test_post'
    COMMENT: str = 'that is comment'

    @classmethod
    def setUpClass(cls):
        super(). setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        cls.group_form = Group.objects.create(
            title=cls.GROUP_TITLE,
            slug=cls.GROUP_SLUG,
            description=cls.GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            text=cls.POST_TEXT,
            group=cls.group_form,
            author=cls.user,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """При отправке валидной формы со страницы создания
        поста reverse('posts:create_post') создаётся новая запись в базе данны.
        """
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group_form.pk,
            'text': 'form_new_text',
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group_form,
                text='form_new_text'
            ).exists()
        )

    def test_edit_post(self):
        """при отправке валидной формы со страницы редактирования поста
        reverse('posts:post_edit', args=('post_id',)) происходит изменение
        поста с post_id в базе данных.
        """
        form_data = {
            'text': 'test_edit_post',
            'group': self.group_form.pk,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group_form.pk
            ).exists()
        )

    def test_create_post_with_image(self):
        """При отправке поста с картинкой через форму
        PostForm создаётся запись в базе данных
        """
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'form_new_text',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
        )
        self.assertTrue(
            Post.objects.filter(
                text='form_new_text',
                image='posts/small.gif'
            ).exists()
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', args=[self.user.username]
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_comment_form_work_correct(self):
        """Комментарий может быть добавлен
         авторизованным пользователем на странице поста """
        form = CommentForm(data={
            'text': self.COMMENT,
        })
        self.assertTrue(form.is_valid())
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form.data,
            follow=True
        )
        self.assertEqual(
            self.post.comments.last().text, form.data['text']
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=[self.post.pk])
        )
