import aiosmtplib
from email.mime.multipart import MIMEMultipart
import os

from ..config import settings


class AsyncSmtpClient:
    def __init__(self):
        self.hostname = 'smtp.gmail.com'
        self.port = 465
        self.username = settings.email_serv_sender.get_secret_value()
        self.password = settings.email_serv_pass.get_secret_value()

    @staticmethod
    def send_email_decorator(func):
        async def wrapper(self, recipient, subject, *args, **kwargs):
            message = MIMEMultipart(
                "alternative")  # Используем "alternative" для поддержки текстового и HTML-содержимого
            message["From"] = self.username
            message["To"] = recipient
            message["Subject"] = subject

            # Получаем результат функции
            result = await func(self, recipient, subject, *args, **kwargs)

            # Проверяем, возвращает ли функция вложение
            if isinstance(result, tuple) and len(result) == 2:
                body, attachment = result
            else:
                body = result
                attachment = None

            # Устанавливаем содержимое тела сообщения (текст и HTML)
            if isinstance(body, str) and "<!DOCTYPE html>" in body:  # Проверяем наличие HTML-контента
                from email.mime.text import MIMEText
                html_message = MIMEText(body, 'html')
                message.attach(html_message)
            else:
                from email.mime.text import MIMEText
                body_message = MIMEText(body, 'plain')  # 'plain' для текстового сообщения
                message.attach(body_message)

            # Прикрепляем файл к сообщению, если он есть
            if attachment:
                message.attach(attachment)

            # Подключаемся и отправляем сообщение
            async with aiosmtplib.SMTP(hostname=self.hostname, port=self.port, timeout=10, use_tls=True,
                                       validate_certs=False) as smtp:
                await smtp.login(self.username, self.password)
                await smtp.send_message(message)

        return wrapper

    @send_email_decorator
    async def send_text_email(self, recipient, subject, body):
        return body

    @send_email_decorator
    async def send_html_email(self, recipient, subject, template_name, **kwargs):
        """
        Отправляет электронное письмо с HTML-содержимым, загруженным из шаблона.
        :param recipient: Адрес электронной почты получателя.
        :param subject: Тема письма.
        :param template_name: Имя файла шаблона (например, 'verify_email.html').
        :param kwargs: Переменные для подстановки в шаблон.
        :return: HTML-код письма.
        """
        template_path = os.path.join('src', 'smtp_mailing', 'templates', template_name)
        try:
            with open(template_path, "r", encoding="utf-8") as html_file:
                html_body = html_file.read()
                # Заменяем переменные в шаблоне
                for key, value in kwargs.items():
                    html_body = html_body.replace(f'{{{{ {key} }}}}', value)
        except FileNotFoundError:
            print(f"Error: HTML template file '{template_name}' not found.")
            return
        return html_body


email_client = AsyncSmtpClient()
