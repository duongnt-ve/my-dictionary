from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import SearchedWord


class WordSearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='testuser@test.com',
            password='test-password-123',
        )

    def test_search_requires_word_field(self):
        response = self.client.post('/api/word/search/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('word', response.json())

    def test_search_rejects_long_word(self):
        response = self.client.post(
            '/api/word/search/',
            {'word': 'x' * 256},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('word', response.json())

    def test_search_rejects_empty_language_code(self):
        response = self.client.post(
            '/api/word/search/',
            {'word': 'hello', 'target_lang': ''},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('target_lang', response.json())

    def test_search_requires_api_key(self):
        response = self.client.post(
            '/api/word/search/',
            {'word': 'hello', 'target_lang': 'es'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.json())
        self.assertIn('GOOGLE_TRANSLATE_API_KEY', response.json()['detail'])

    def test_search_history_requires_authentication(self):
        response = self.client.get('/api/word/search-history/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_search_history_returns_empty_initially(self):
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/word/search-history/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'searches': []})

    def test_search_history_shows_only_user_searches(self):
        other_user = get_user_model().objects.create_user(
            username='otheruser@test.com',
            password='other-password-456',
        )
        SearchedWord.objects.create(
            user=self.user,
            content='hello',
            result={'word': 'hello', 'translation': 'hola', 'target_lang': 'es'},
        )
        SearchedWord.objects.create(
            user=other_user,
            content='goodbye',
            result={'word': 'goodbye', 'translation': 'adiós', 'target_lang': 'es'},
        )
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/word/search-history/', format='json')
        self.assertEqual(response.status_code, 200)
        searches = response.json()['searches']
        self.assertEqual(len(searches), 1)
        self.assertEqual(searches[0]['word'], 'hello')

