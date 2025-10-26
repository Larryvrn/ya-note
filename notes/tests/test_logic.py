# notes/tests/test_logic.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    """
    Тестирование логики создания заметок в приложении.

    Проверяет сценарии создания заметок для различных типов пользователей,
    включая анонимных пользователей, авторизованных пользователей,
    а также обработку дублирующихся slug.
    """

    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'test-note'

    @classmethod
    def setUpTestData(cls):
        """
        Подготавливает тестовые данные для создания заметок.

        Инициализирует:
        - URL для создания заметки
        - Тестового пользователя
        - Авторизованный клиент
        - Данные формы для POST-запроса
        """
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Автор заметки')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG
        }

    def test_anonymous_user_cant_create_note(self):
        """
        Проверяет, что анонимный пользователь не может создать заметку.

        Ожидаемое поведение:
        - POST-запрос от анонимного пользователя игнорируется
        - Количество заметок в базе данных остается равным 0
        - Пользователь перенаправляется на страницу авторизации
        """
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """
        Проверяет успешное создание заметки авторизованным пользователем.

        Проверяет:
        - Редирект на страницу успеха после создания
        - Увеличение количества заметок в базе данных на 1
        - Корректное сохранение всех атрибутов заметки
        - Связь заметки с автором

        Атрибуты проверки:
        - title: заголовок заметки
        - text: содержимое заметки
        - slug: уникальный идентификатор
        - author: пользователь-создатель
        """
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_user_cant_use_duplicate_slug(self):
        """
        Проверяет обработку дублирующихся slug при создании заметок.

        Сценарий:
        1. Создается первая заметка с определенным slug
        2. Пытается создать вторая заметка с таким же slug
        3. Проверяется отказ в создании и вывод ошибки валидации

        Ожидаемый результат:
        - Форма возвращает ошибку валидации для поля slug
        - Вторая заметка не создается
        - В базе данных остается только одна заметка
        """
        # Создаём первую заметку
        self.auth_client.post(self.url, data=self.form_data)
        # Пытаемся создать вторую заметку с тем же slug
        response = self.auth_client.post(self.url, data=self.form_data)
        form = response.context['form']
        self.assertFormError(
            form=form,
            field='slug',
            errors=self.NOTE_SLUG + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


class TestNoteEditDelete(TestCase):
    """
    Тестирование логики редактирования и удаления заметок.

    Проверяет права доступа к операциям редактирования и удаления
    для авторов заметок и других пользователей.
    """

    NOTE_TITLE = 'Исходный заголовок'
    NOTE_TEXT = 'Исходный текст'
    NOTE_SLUG = 'original-note'
    NEW_TITLE = 'Обновлённый заголовок'
    NEW_TEXT = 'Обновлённый текст'
    NEW_SLUG = 'updated-note'

    @classmethod
    def setUpTestData(cls):
        """
        Подготавливает тестовые данные для операций редактирования и удаления.

        Инициализирует:
        - Автора заметки и другого пользователя
        - Тестовую заметку с исходными данными
        - Авторизованные клиенты для автора и читателя
        - URL для операций редактирования и удаления
        - Данные для обновления заметки
        """
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': cls.NEW_TITLE,
            'text': cls.NEW_TEXT,
            'slug': cls.NEW_SLUG
        }

    def test_author_can_delete_note(self):
        """
        Проверяет возможность автора удалить свою заметку.

        Ожидаемое поведение:
        - DELETE-запрос выполняется успешно
        - Происходит редирект на страницу успешного действия
        - Заметка удаляется из базы данных
        - Количество заметок становится равным 0
        """
        response = self.author_client.delete(self.delete_url)
        # Исправлено: редирект на страницу успеха, а не на список заметок
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """
        Проверяет запрет удаления чужих заметок.

        Сценарий:
        - Пользователь, не являющийся автором, пытается удалить заметку
        - Система возвращает ошибку 404 (Not Found)

        Ожидаемый результат:
        - Заметка остается в базе данных
        - Количество заметок не изменяется
        """
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """
        Проверяет возможность автора редактировать свою заметку.

        Проверяет:
        - Успешное выполнение POST-запроса на редактирование
        - Редирект после успешного обновления
        - Корректное обновление всех полей заметки
        - Сохранение связи с автором

        Обновляемые поля:
        - title: заголовок заметки
        - text: содержимое заметки
        - slug: уникальный идентификатор
        """
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_TITLE)
        self.assertEqual(self.note.text, self.NEW_TEXT)
        self.assertEqual(self.note.slug, self.NEW_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        """
        Проверяет запрет редактирования чужих заметок.

        Сценарий:
        - Пользователь, не являющийся автором, пытается редактировать заметку
        - Система возвращает ошибку 404 (Not Found)
        - Данные заметки остаются неизменными

        Ожидаемый результат:
        - Все поля заметки сохраняют исходные значения
        - Автор заметки не изменяется
        """
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)
        self.assertEqual(self.note.author, self.author)
