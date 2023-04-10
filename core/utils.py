import smtplib
from contextvars import ContextVar

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.template import loader, Context, Template

from .models import Client


class CheckUserPosition:
    def __init__(self):
        self.employee: ContextVar[Client | None] = ContextVar('user', default=None)

    def set_user(self, request):
        if request.user:
            if request.user.employer:
                self.employee.set(request.user)
                request.user = request.user.employer


IsEmployee = CheckUserPosition()


def send_email(recip: str, subject: str, context: dict, template_name: str):
    with open(f"./core/templates/{template_name}", 'r') as file:
        html_template = file.read()

    message = Template(html_template).render(Context(context))

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = settings.EMAIL_HOST_USER
    msg['To'] = recip
    msg.attach(MIMEText(message, 'html'))

    smtp = None
    try:
        smtp = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
        smtp.ehlo()
        smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        smtp.sendmail(settings.EMAIL_HOST_USER, recip, msg.as_string())
        smtp.quit()
    except Exception:
        if smtp:
            smtp.quit()
