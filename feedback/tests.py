from unittest.mock import patch

from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class EmailServiceTests(APITestCase):
    def test_send_email_success(self):
        """Recieve 200 status code when sending email with valid inputs"""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "message": "This is a test message.",
        }
        response = self.client.post(reverse("send_email"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Email sent successfully!")
        self.assertEqual(len(mail.outbox), 1)

    def test_send_email_invalid(self):
        """Recieve 400 status code when sending email with invalid inputs"""
        data = {
            "name": "",
            "email": "invalid-email",
            "message": "",
        }
        response = self.client.post(reverse("send_email"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("django.core.mail.EmailMessage.send")
    def test_send_email_error(self, mock_send):
        """Recieve 500 status code when SMTP error occurs during email send"""
        mock_send.side_effect = Exception("SMTP error")

        data = {
            "name": "Test User",
            "email": "test@example.com",
            "message": "This is a test message.",
        }
        response = self.client.post(reverse("send_email"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "SMTP error")
