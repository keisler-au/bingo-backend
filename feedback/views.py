import logging
import os
from smtplib import SMTPException

import sentry_sdk
from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("__name__")


class SendEmailView(APIView):
    def post(self, request):
        """Send email with message from Feedback box"""
        response = Response(
            {"error": "Message wasn't sent and no 500 raised"},
            status=status.HTTP_400_BAD_REQUEST,
        )

        logger.error(f"Message is {request.data}")
        message = request.data

        subject = "Bingo App Feedback"
        body = f"Message:\n{message}"
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=os.getenv("HOST_USER_EMAIL"),
            to=[os.getenv("HOST_USER_EMAIL")],
        )

        try:
            email.send(fail_silently=False)
            response = Response(
                {"message": "Email sent successfully!"}, status=status.HTTP_200_OK
            )
        except SMTPException as e:
            logger.error(f"SMTP error occurred when sending email: {str(e)}")
            sentry_sdk.capture_exception(e)
            response = Response(
                {"error": f"SMTP error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Error occurred when sending email: {str(e)}")
            sentry_sdk.capture_exception(e)
            response = Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return response
