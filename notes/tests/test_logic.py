from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestNoteLogic(TestCase):
    """Проверка логики работы с заметками."""

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

    def test_authorized_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        self.client.force_login(self.author)
        url = reverse('notes:add')
        note_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note'
        }
        response = self.client.post(url, data=note_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.get(slug='new-note')
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_cannot_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        url = reverse('notes:add')
        note_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note'
        }
        response = self.client.post(url, data=note_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(
            response,
            expected_url,
            status_code=302,
            target_status_code=200
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_cannot_create_duplicate_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        self.client.force_login(self.author)
        url = reverse('notes:add')
        note_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': self.note.slug
        }
        response = self.client.post(url, data=note_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('slug', form.errors)
        self.assertIn(f'{self.note.slug} - такой slug уже существует, придумайте уникальное значение!', 
                      form.errors['slug'])
        self.assertEqual(Note.objects.count(), 1)

    def test_slug_auto_generation(self):
        """
        Если при создании заметки не заполнен slug, 
        он формируется автоматически через slugify.
        """
        self.client.force_login(self.author)
        url = reverse('notes:add')
        title = 'Новая заметка с длинным названием'
        note_data = {
            'title': title,
            'text': 'Текст новой заметки',
            'slug': ''
        }
        response = self.client.post(url, data=note_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        expected_slug = slugify(title)[:100]
        new_note = Note.objects.exclude(pk=self.note.pk).first()
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_own_note(self):
        """Пользователь может редактировать свою заметку."""
        self.client.force_login(self.author)
        url = reverse('notes:edit', args=(self.note.slug,))
        new_data = {
            'title': 'Обновлённый заголовок',
            'text': 'Обновлённый текст',
            'slug': 'updated-slug'
        }
        response = self.client.post(url, data=new_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, new_data['title'])
        self.assertEqual(self.note.text, new_data['text'])
        self.assertEqual(self.note.slug, new_data['slug'])

    def test_author_can_delete_own_note(self):
        """Пользователь может удалить свою заметку."""
        self.client.force_login(self.author)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cannot_edit_foreign_note(self):
        """Пользователь не может редактировать чужую заметку."""
        self.client.force_login(self.reader)
        url = reverse('notes:edit', args=(self.note.slug,))
        new_data = {
            'title': 'Обновлённый заголовок',
            'text': 'Обновлённый текст',
            'slug': 'updated-slug'
        }
        response = self.client.post(url, data=new_data)
        self.assertEqual(response.status_code, 404)
        self.note.refresh_from_db()
        self.assertNotEqual(self.note.title, new_data['title'])

    def test_user_cannot_delete_foreign_note(self):
        """Пользователь не может удалить чужую заметку."""
        self.client.force_login(self.reader)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Note.objects.count(), 1)
