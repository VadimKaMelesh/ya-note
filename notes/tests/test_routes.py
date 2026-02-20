from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тестирование доступности маршрутов."""

    @classmethod
    def setUpTestData(cls):
        """Создание данных для всех тестов класса."""
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок заметки',
            text='Текст заметки',
            slug='test-slug',
            author=cls.author
        )

    def test_home_availability(self):
        """Главная страница доступна анонимному пользователю."""
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_auth_pages_availability_for_anonymous(self):
        """
        Страницы регистрации, входа и выхода доступны всем пользователям.
        """
        urls = [
            reverse('users:login'),
            reverse('users:logout'),
            reverse('users:signup'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                if url == reverse('users:logout'):
                    self.assertEqual(response.status_code, 405)
                else:
                    self.assertEqual(response.status_code, 200)

    def test_pages_availability_for_authorized(self):
        """
        Аутентифицированному пользователю доступны:
        - список заметок
        - страница успешного добавления
        - страница добавления заметки
        """
        self.client.force_login(self.author)
        urls = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_note_pages_availability_for_author(self):
        """
        Страницы отдельной заметки, удаления и редактирования доступны автору.
        """
        self.client.force_login(self.author)
        urls = [
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,)),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_note_pages_not_available_for_reader(self):
        """
        Другой пользователь не может зайти на страницы чужой заметки (404).
        """
        self.client.force_login(self.reader)
        urls = [
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,)),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)

    def test_anonymous_redirect_for_protected_pages(self):
        """
        Анонимный пользователь перенаправляется на страницу логина
        при попытке зайти на защищённые страницы.
        """
        login_url = reverse('users:login')
        protected_urls = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,)),
        ]
        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                expected_url = f'{login_url}?next={url}'
                self.assertRedirects(
                    response,
                    expected_url,
                    status_code=302,
                    target_status_code=200
                )
