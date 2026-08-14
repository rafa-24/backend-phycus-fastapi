from jinja2 import Environment, FileSystemLoader
import smtplib
import os
import requests
import resend
import requests

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

        # importar resend
        resend.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("SMTP_FROM", "onboarding@resend.dev")

        #self.from_email_mailgun = "postmaster@sandbox1f4c9fdf3d2349f08f4ff13de10c77ce.mailgun.org"

        # API KEY MAILGUM
        self.mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        self.mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        self.mailgun_base_url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
        self.mailgun_from = os.getenv("FROM_MAILGUN")

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


    def send_email_resend(self, to_email: str, subject: str, html_content: str):
        try:
            resend.Emails.send({
                "from": self.from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content
            })

            print(f'correo enviado correctamente a {to_email} via Resend')
        except Exception as e:
            print(f"Error sending email via Resend: {e}")

    def send_email_mailgum(self, to_email: str, subject: str, html_content: str):
        try:
            response = requests.post(
                self.mailgun_base_url,
                auth=("api", f"{self.mailgun_api_key}"),
                data = {
                    "from": self.mailgun_from,
                    "to": to_email,
                    "subject": subject,
                    "html": html_content
                }
            )

            if response.status_code == 200:
                print(f'correo enviado correctamente a {to_email} via Mailgun')
                print(response.json())
            else:
                print(f'Error al enviar correo a {to_email} via Mailgun. Status code: {response.status_code}')
                print(response.text)    
        except Exception as e:
            print(f"Error sending email via Mailgun: {e}")



