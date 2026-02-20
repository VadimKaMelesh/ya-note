from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    """Проверка содержимого страниц."""

    @classmethod
    def setUpTestData(cls):
        """Создание данных для всех тестов класса."""
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        
        cls.author_note = Note.objects.create(
            title='Заметка автора',
            text='Текст заметки автора',
            slug='author-note',
            author=cls.author
        )
        
        cls.reader_note = Note.objects.create(
            title='Заметка читателя',
            text='Текст заметки читателя',
            slug='reader-note',
            author=cls.reader
        )

    def test_note_in_context_on_list_page(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок
        в списке object_list в словаре context.
        """
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertIn('object_list', response.context)
        object_list = response.context['object_list']
        self.assertIn(self.author_note, object_list)
        self.assertEqual(len(object_list), 1)

    def test_notes_list_for_author(self):
        """
        В список заметок одного пользователя не попадают заметки другого.
        """
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.author_note, object_list)
        self.assertNotIn(self.reader_note, object_list)

        self.client.force_login(self.reader)
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.reader_note, object_list)
        self.assertNotIn(self.author_note, object_list)

    def test_form_in_create_page(self):
        """На страницу создания заметки передаётся форма."""
        self.client.force_login(self.author)
        url = reverse('notes:add')
        response = self.client.get(url)
        self.assertIn('form', response.context)

    def test_form_in_edit_page(self):
        """На страницу редактирования заметки передаётся форма."""
        self.client.force_login(self.author)
        url = reverse('notes:edit', args=(self.author_note.slug,))
        response = self.client.get(url)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertEqual(form.instance, self.author_note)
