from jinja2 import Environment, FileSystemLoader

import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config.settings import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM
)


class EmailService:

    def __init__(self):

        self.env = Environment(
            loader=FileSystemLoader(
                "app/templates/mails"
            )
        )

    def render_template(
        self,
        template_name: str,
        context: dict
    ):

        template = self.env.get_template(
            template_name
        )

        return template.render(
            **context
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ):

        message = MIMEMultipart()

        message["From"] = SMTP_FROM
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(
            MIMEText(
                html_content,
                "html"
            )
        )

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                SMTP_USER,
                SMTP_PASSWORD
            )

            server.send_message(
                message
            )