"""Модуль тестирования маршрутов (URL) приложения заметок.

Содержит тесты для проверки:
- Доступности публичных страниц для всех пользователей
- Прав доступа к защищенным страницам для авторов и других пользователей
- Редиректов анонимных пользователей на страницу авторизации
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model  # type: ignore
from django.test import TestCase  # type: ignore
from django.urls import reverse  # type: ignore

# Импортируем класс модели новостей, комментариев
from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):
    """
    Тестирование доступности маршрутов приложения заметок.

    Проверяет корректность работы системы прав доступа
    для различных типов пользователей (анонимные, авторы, читатели).
    """

    @classmethod
    def setUpTestData(cls):
        """
        Подготавливает тестовые данные для проверки маршрутов.

        Создает:
        - Автора заметки
        - Обычного пользователя (читателя)
        - Тестовую заметку для проверки доступа
        """
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        # От имени одного пользователя создаём комментарий к новости:
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='zametka',
            author=cls.author
        )

    def test_pages_availability(self):
        """
        Тестирует доступность публичных страниц для всех пользователей.

        Проверяет, что главная страница и страницы аутентификации
        возвращают статус 200 (OK) для анонимных пользователей.

        Тестируемые страницы:
        - Главная страница (notes:home)
        - Страница входа (users:login)
        - Страница регистрации (users:signup)
        """
        # Создаём набор тестовых данных - кортеж кортежей.
        # Каждый вложенный кортеж содержит два элемента:
        # имя пути и позиционные аргументы для функции reverse().
        urls = (
            # Путь для главной страницы не принимает
            # никаких позиционных аргументов,
            # поэтому вторым параметром ставим None.
            ('notes:home', None),
            ('users:login', None),
            ('users:signup', None),
        )
        # Итерируемся по внешнему кортежу
        # и распаковываем содержимое вложенных кортежей:
        for name, args in urls:
            with self.subTest(name=name):
                # Передаём имя и позиционный аргумент в reverse()
                # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_notes_edit_and_delete(self):
        """
        Тестирует права доступа к защищенным страницам заметок.

        Проверяет, что автор имеет доступ к страницам редактирования,
        удаления и деталей своей заметки, а другие пользователи получают 404.

        Тестируемые страницы:
        - Редактирование заметки (notes:edit)
        - Удаление заметки (notes:delete)
        - Детали заметки (notes:detail)
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in (
                'notes:edit',
                'notes:delete',
                'notes:detail',
            ):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Тестирует редиректы анонимных пользователей на страницу авторизации.

        Проверяет, что при попытке доступа к защищенным страницам
        анонимные пользователи перенаправляются на страницу входа
        с параметром 'next', содержащим исходный URL.

        Тестируемые страницы:
        - Все защищенные страницы приложения заметок
        """
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in (
                'notes:edit',
                'notes:delete',
                'notes:add',
                'notes:list',
                'notes:detail',
                'notes:success'
        ):
            with self.subTest(name=name):
                # Получаем адрес страницы редактирования
                # или удаления комментария:
                if name in ('notes:edit', 'notes:delete', 'notes:detail'):
                    url = reverse(name, args=(self.note.slug,))
                else:
                    url = reverse(name)
                # Получаем ожидаемый адрес страницы логина,
                # на который будет перенаправлен пользователь.
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)
