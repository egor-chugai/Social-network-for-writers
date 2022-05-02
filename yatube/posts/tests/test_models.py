from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    GROUP_TITLE: str = 'test_group'
    GROUP_SLUG: str = 'test_slug'
    GROUP_DESCRIPTION: str = 'test_description'
    POST_TEXT: str = 'test_post'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title=cls.GROUP_TITLE,
            slug=cls.GROUP_SLUG,
            description=cls.GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.POST_TEXT,
        )

    def test_models_have_correct_object_names(self):
        """У моделей Post, Group корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_name = {
            'test_post': post,
            'test_group': group,
        }
        for expect, model in expected_object_name.items():
            with self.subTest(field=expect):
                self.assertEqual(str(model), expect)
