"""Модуль тестирования контента и функциональности приложения заметок.

Содержит тесты для проверки:
- Отображения списка заметок для разных пользователей
- Наличия форм на страницах создания и редактирования заметок
"""
import pytest  # type: ignore

from django.urls import reverse  # type: ignore
from pytest_lazy_fixtures import lf  # type: ignore

from notes.forms import NoteForm  # type: ignore


@pytest.mark.parametrize(
    # Задаём названия для параметров:
    'parametrized_client, note_in_list',
    (
        # Передаём фикстуры в параметры при помощи "ленивых фикстур":
        (lf('author_client'), True),
        (lf('not_author_client'), False),
    )
)
def test_notes_list_for_different_users(
    note, parametrized_client, note_in_list
):
    """
    Тест отображения списка заметок для разных пользователей.

    Проверяет, что автор видит свою заметку в списке,
    а другой пользователь - нет.

    Args:
        note: Фикстура создания заметки
        parametrized_client: Параметризованный клиент (автор или не автор)
        note_in_list (bool): Ожидаемое наличие заметки в списке
    """
    # Используем фикстуру заметки и параметры из декоратора:
    url = reverse('notes:list')
    # Выполняем запрос от имени параметризованного клиента:
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    # Проверяем истинность утверждения "заметка есть в списке":
    assert (note in object_list) is note_in_list


@pytest.mark.parametrize(
    # В качестве параметров передаём name и args для reverse.
    'name, args',
    (
        # Для тестирования страницы создания заметки
        # никакие дополнительные аргументы для reverse() не нужны.
        ('notes:add', None),
        # Для тестирования страницы редактирования заметки нужен slug заметки.
        ('notes:edit', lf('slug_for_args'))
    )
)
def test_pages_contains_form(author_client, name, args):
    """
    Тест наличия формы на страницах создания и редактирования заметок.

    Проверяет, что на страницах создания и редактирования заметки
    присутствует форма правильного типа.

    Args:
        author_client: Клиент авторизованного автора
        name (str): Имя URL-паттерна
        args: Аргументы для reverse (slug заметки или None)
    """
    # Формируем URL.
    url = reverse(name, args=args)
    # Запрашиваем нужную страницу:
    response = author_client.get(url)
    # Проверяем, есть ли объект формы в словаре контекста:
    assert 'form' in response.context
    # Проверяем, что объект формы относится к нужному классу.
    assert isinstance(response.context['form'], NoteForm)
