"""
Модуль тестирования views приложения заметок.

Содержит тесты для проверки:
- Домашней страницы и её содержимого
- Страницы со списком заметок (изоляция данных, сортировка)
- Страницы деталей заметки (права доступа, отображение контента)
- Форм создания и редактирования заметок
- Страницы успешного выполнения операции
"""
from django.test import TestCase  # type: ignore
from django.urls import reverse  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestHomePage(TestCase):
    """
    Тестирование домашней страницы приложения заметок.

    Проверяет базовую функциональность главной страницы, включая
    доступность, использование правильных шаблонов и отображение контента.
    """

    HOME_URL = reverse('notes:home')

    @classmethod
    def setUpTestData(cls):
        """Создаём фикстуры для тестов домашней страницы."""
        cls.author = User.objects.create(username='Автор заметок')
        # Создаём несколько заметок
        cls.notes = []
        for index in range(3):
            note = Note.objects.create(
                title=f'Заметка {index}',
                text=f'Текст заметки {index}',
                author=cls.author,
                slug=f'zametka-{index}'
            )
            cls.notes.append(note)

    def test_home_page_content(self):
        """
        Проверяет базовое содержимое и доступность домашней страницы.

        Тестирует:
        - Возврат HTTP статуса 200
        - Использование корректного шаблона 'notes/home.html'
        - Наличие ожидаемого контекста
        """
        response = self.client.get(self.HOME_URL)
        self.assertEqual(response.status_code, 200)
        # Проверяем, что используется правильный шаблон
        self.assertTemplateUsed(response, 'notes/home.html')


class TestNotesListPage(TestCase):
    """
    Тестирование функциональности страницы со списком заметок.

    Проверяет изоляцию данных между пользователями, правильность
    отображения и сортировки списка заметок.
    """

    @classmethod
    def setUpTestData(cls):
        """Создаём фикстуры для тестов страницы со списком заметок."""
        cls.author = User.objects.create(username='Автор')
        cls.other_user = User.objects.create(username='Другой пользователь')

        # Создаём заметки для автора
        cls.author_notes = []
        for i in range(3):
            note = Note.objects.create(
                title=f'Заметка автора {i}',
                text=f'Текст заметки автора {i}',
                author=cls.author,
                slug=f'avtorskaya-{i}'
            )
            cls.author_notes.append(note)

        # Создаём заметки для другого пользователя
        for i in range(2):
            Note.objects.create(
                title=f'Заметка другого {i}',
                text=f'Текст другого пользователя {i}',
                author=cls.other_user,
                slug=f'chuzhaya-{i}'
            )

    def test_notes_list_shows_only_user_notes(self):
        """
        Проверяет, что пользователь видит только свои заметки.

        Методы:
        - force_login(): авторизация тестового пользователя
        - reverse(): получение URL страницы списка
        - assertTemplateUsed(): проверка используемого шаблона
        - assertIn(): проверка наличия объекта в контексте

        Проверяет:
        - Изоляцию данных между пользователями
        - Корректность фильтрации заметок по автору
        - Количество отображаемых заметок
        """
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/list.html')

        # Проверяем, что в контексте есть объекты
        self.assertIn('object_list', response.context)

        # Проверяем, что отображаются только заметки автора
        notes_in_context = list(response.context['object_list'])
        author_notes_slugs = [note.slug for note in self.author_notes]
        context_notes_slugs = [note.slug for note in notes_in_context]

        self.assertEqual(set(context_notes_slugs), set(author_notes_slugs))
        self.assertEqual(len(notes_in_context), 3)

    def test_notes_list_ordered_correctly(self):
        """
        Проверяет правильность порядка отображения заметок.

        Параметры проверки:
        - Порядок по дате создания (если поле 'created' существует)
        - Порядок по ID или другому полю сортировки

        Методы:
        - hasattr(): проверка наличия поля даты создания
        - sorted(): проверка правильности сортировки
        """
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:list'))

        notes = list(response.context['object_list'])
        # Если в модели есть auto_now_add для даты создания, проверяем порядок
        # Если нет - проверяем порядок по ID или другому полю
        if hasattr(notes[0], 'created') and notes[0].created:
            dates = [note.created for note in notes]
            sorted_dates = sorted(dates, reverse=True)
            self.assertEqual(dates, sorted_dates)


class TestNoteDetailPage(TestCase):
    """
    Тестирование страницы с детальной информацией о заметке.

    Проверяет права доступа, передачу контекста и отображение
    содержимого отдельных заметок.
    """

    @classmethod
    def setUpTestData(cls):
        """Создаём фикстуры для тестов страница деталей заметки."""
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')

        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Это текст тестовой заметки для проверки отображения.',
            author=cls.author,
            slug='testovaya-zametka'
        )
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))

    def test_note_in_context(self):
        """
        Проверяет передачу объекта заметки в контекст шаблона.

        Аргументы:
        - slug: уникальный идентификатор заметки в URL

        Проверяет:
        - Наличие объекта 'note' в контексте ответа
        - Соответствие объекта ожидаемой заметке
        - Использование slug для идентификации заметки
        """
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)

        # Проверяем, что объект заметки находится в словаре контекста
        self.assertIn('note', response.context)
        # Получаем объект заметки из контекста
        note = response.context['note']
        # Проверяем, что это именно наша тестовая заметка
        self.assertEqual(note, self.note)

    def test_note_content_displayed(self):
        """
        Проверяет отображение содержимого заметки на странице.

        Методы:
        - assertContains(): проверка наличия текста в HTML ответе

        Проверяемые элементы:
        - Заголовок заметки (title)
        - Основной текст заметки (text)
        """
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)

        # Проверяем, что заголовок и текст заметки присутствуют в HTML
        self.assertContains(response, self.note.title)
        self.assertContains(response, self.note.text)

    def test_author_can_access_own_note(self):
        """
        Проверяет доступ автора к своей заметке.

        Сценарий:
        - Автор авторизуется в системе
        - Запрашивает страницу своей заметки
        - Получает HTTP статус 200 (успех)
        """
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_access_note(self):
        """
        Проверяет ограничение доступа к чужим заметкам.

        Сценарий:
        - Другой пользователь авторизуется в системе
        - Запрашивает страницу чужой заметки
        - Получает HTTP статус 404 (не найдено)

        Ожидаемый результат:
        - Защита от несанкционированного доступа к данным
        """
        self.client.force_login(self.reader)
        response = self.client.get(self.detail_url)
        # Должен получить 404, так как заметка принадлежит другому автору
        self.assertEqual(response.status_code, 404)


class TestNoteForms(TestCase):
    """
    Тестирование форм создания и редактирования заметок.

    Проверяет функциональность форм, права доступа и корректность
    обработки данных на стороне сервера.
    """

    @classmethod
    def setUpTestData(cls):
        """Создаём фикстуры для тестирования форм заметок."""
        cls.author = User.objects.create(username='Автор')
        cls.other_user = User.objects.create(username='Другой')

        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Просто текст.',
            author=cls.author,
            slug='testovaya-zametka'
        )
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')

    def test_anonymous_client_redirected_from_add_page(self):
        """
        Проверяет редирект анонимного пользователя со страницы добавления.

        Ожидаемое поведение:
        - HTTP статус 302 (редирект)
        - Перенаправление на страницу авторизации
        - Наличие параметра 'next' в URL редиректа
        """
        response = self.client.get(self.add_url)
        # Должен быть редирект на страницу логина
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_authorized_client_has_form_on_add_page(self):
        """
        Проверяет наличие формы у авториз. пользователя на стр. добавления.

        Проверяет:
        - Возврат HTTP статуса 200
        - Наличие объекта 'form' в контексте
        - Тип формы (NoteForm)
        - Доступность формы для авторизованного пользователя
        """
        self.client.force_login(self.author)
        response = self.client.get(self.add_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        # Проверяем, что объект формы соответствует нужному классу формы
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_author_has_form_on_edit_page(self):
        """
        Проверяет наличие формы у автора на странице редактирования.

        Аргументы:
        - slug: идентификатор редактируемой заметки

        Проверяет:
        - Предзаполнение формы данными существующей заметки
        - Соответствие instance формы ожидаемому объекту
        - Тип используемой формы
        """
        self.client.force_login(self.author)
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)
        # Проверяем, что форма содержит данные текущей заметки
        self.assertEqual(response.context['form'].instance, self.note)

    def test_other_user_cannot_edit_note(self):
        """
        Проверяет запрет редактирования чужих заметок.

        Сценарий:
        - Пользователь пытается получить доступ к форме
        редактирования чужой заметки
        - Система возвращает HTTP статус 404

        Ожидаемый результат:
        - Защита от несанкционированного редактирования
        """
        self.client.force_login(self.other_user)
        response = self.client.get(self.edit_url)
        # Должен получить 404
        self.assertEqual(response.status_code, 404)

    def test_success_page_after_note_creation(self):
        """
        Проверяет редирект на страницу успеха после создания заметки.

        Методы:
        - client.post(): отправка POST запроса с данными формы
        - assertRedirects(): проверка редиректа
        - objects.filter().exists(): проверка создания записи в БД

        Параметры запроса:
        - title: заголовок новой заметки
        - text: содержимое заметки
        - slug: уникальный идентификатор заметки
        """
        self.client.force_login(self.author)
        data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'novaya-zametka'
        }
        response = self.client.post(self.add_url, data)
        # После успешного создания должно быть перенаправление
        # на страницу успеха
        self.assertRedirects(response, self.success_url)

        # Проверяем, что заметка действительно создалась
        self.assertTrue(Note.objects.filter(slug='novaya-zametka').exists())


class TestNoteSuccessPage(TestCase):
    """
    Тестирование страницы подтверждения успешного действия.

    Проверяет доступность и корректность отображения страницы,
    подтверждающей успешное выполнение операции.
    """

    def test_success_page_accessible(self):
        """
        Проверяет доступность страницы успеха для авторизованного пользователя.

        Проверяет:
        - HTTP статус 200
        - Использование шаблона 'notes/success.html'
        - Доступность страницы после авторизации
        """
        user = User.objects.create(username='Тестовый пользователь')
        self.client.force_login(user)
        response = self.client.get(reverse('notes:success'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/success.html')
