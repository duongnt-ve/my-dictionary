from django.test import SimpleTestCase


class WordsViewTests(SimpleTestCase):
    def test_words_endpoint_returns_sample_words(self):
        response = self.client.get('/api/words/')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'words': ['hello', 'world']})
