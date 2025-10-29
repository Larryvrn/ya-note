"""Модуль с фикстурами для тестирования приложения заметок.

Содержит фикстуры для создания тестовых данных:

Пользователи (автор и не автор)

Аутентифицированные клиенты

Тестовые заметки

Данные для форм
"""
import pytest  # type: ignore

from django.test.client import Client  # type: ignore

from notes.models import Note  # type: ignore


@pytest.fixture
def author(django_user_model):
    """
    Фикстура для создания пользователя-автора.

    Args:
        django_user_model: Встроенная фикстура для модели пользователей Django

    Returns:
        User: Созданный пользователь с username 'Автор'
    """
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    """
    Фикстура для создания пользователя, не являющегося автором.

    Args:
        django_user_model: Встроенная фикстура для модели пользователей Django

    Returns:
        User: Созданный пользователь с username 'Не автор'
    """
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author):
    """
    Фикстура для создания клиента авторизованного автора.

    Args:
        author: Фикстура создания пользователя-автора

    Returns:
        Client: Клиент Django с авторизованным автором
    """
    # Создаём новый экземпляр клиента, чтобы не менять глобальный.
    client = Client()
    # Логиним автора в клиенте.
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    """
    Фикстура для создания клиента авторизованного пользователя (не автора).

    Args:
        not_author: Фикстура создания пользователя, не являющегося автором

    Returns:
        Client: Клиент Django с авторизованным пользователем (не автором)
    """
    client = Client()
    # Логиним обычного пользователя в клиенте.
    client.force_login(not_author)
    return client


@pytest.fixture
def note(author):
    """
    Фикстура для создания тестовой заметки.

    Args:
        author: Фикстура создания пользователя-автора

    Returns:
        Note: Созданный объект заметки
    """
    # Создаём объект заметки.
    note = Note.objects.create(
        title='Заголовок',
        text='Текст заметки',
        slug='note-slug',
        author=author,
    )
    return note


@pytest.fixture
def slug_for_args(note):
    """
    Фикстура для получения slug заметки в виде кортежа.

    Args:
        note: Фикстура создания заметки

    Returns:
        tuple: Кортеж, содержащий slug заметки
    """
    # И возвращает кортеж, который содержит slug заметки.
    # На то, что это кортеж, указывает запятая в конце выражения.
    return (note.slug,)


@pytest.fixture
def form_data():
    """
    Фикстура для получения данных формы.

    Returns:
        dict: Словарь с данными для формы заметки
    """
    return {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug'
    }
