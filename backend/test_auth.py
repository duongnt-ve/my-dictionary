from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.authentication import JWTAuthentication


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.credentials = {'email': 'User@example.com', 'password': 'a-long-unique-password-42'}

    def test_signup_signin_refresh_and_signout(self):
        signup = self.client.post('/api/auth/signup/', self.credentials, format='json')
        self.assertEqual(signup.status_code, 201)
        self.assertEqual(signup.json(), {'email': 'user@example.com'})
        self.assertTrue(get_user_model().objects.get(username='user@example.com').check_password(
            self.credentials['password']
        ))

        signin = self.client.post('/api/auth/signin/', self.credentials, format='json')
        self.assertEqual(signin.status_code, 200)
        self.assertIn('access', signin.json())
        refresh = signin.json()['refresh']

        self.assertEqual(self.client.post(
            '/api/auth/refresh/', {'refresh': refresh}, format='json'
        ).status_code, 200)
        self.assertEqual(self.client.post(
            '/api/auth/signout/', {'refresh': refresh}, format='json'
        ).status_code, 204)
        access = JWTAuthentication().get_validated_token(signin.json()['access'])
        self.assertEqual(JWTAuthentication().get_user(access).email, 'user@example.com')
        self.assertEqual(self.client.post(
            '/api/auth/refresh/', {'refresh': refresh}, format='json'
        ).status_code, 401)
        self.assertEqual(self.client.post(
            '/api/auth/signout/', {'refresh': refresh}, format='json'
        ).status_code, 401)

    def test_signup_rejects_duplicate_email_and_weak_password(self):
        self.client.post('/api/auth/signup/', self.credentials, format='json')
        duplicate = self.client.post('/api/auth/signup/', {
            'email': 'USER@example.com', 'password': 'another-unique-password-42',
        }, format='json')
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn('email', duplicate.json())

        weak = self.client.post('/api/auth/signup/', {
            'email': 'other@example.com', 'password': '123',
        }, format='json')
        self.assertEqual(weak.status_code, 400)
        self.assertIn('password', weak.json())

    def test_invalid_credentials_and_tokens_are_rejected(self):
        self.client.post('/api/auth/signup/', self.credentials, format='json')
        signin = self.client.post('/api/auth/signin/', {
            'email': self.credentials['email'], 'password': 'wrong',
        }, format='json')
        self.assertEqual(signin.status_code, 401)
        self.assertEqual(self.client.post(
            '/api/auth/signout/', {}, format='json'
        ).status_code, 400)
        self.assertEqual(self.client.post(
            '/api/auth/signout/', {'refresh': 'not-a-token'}, format='json'
        ).status_code, 401)
