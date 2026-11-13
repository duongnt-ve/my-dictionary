import os
from google.cloud import translate_v2
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView

from .models import SearchedWord


def get_translate_client():
    api_key = os.environ.get('GOOGLE_TRANSLATE_API_KEY')
    if not api_key:
        raise ValueError('GOOGLE_TRANSLATE_API_KEY not set in environment.')
    return translate_v2.Client(api_key=api_key)


class SearchWordView(APIView):
    permission_classes = []

    def post(self, request):
        word = request.data.get('word', '').strip()
        target_lang = request.data.get('target_lang', 'en').strip()

        if not word:
            return Response({'word': ['This field is required.']}, status=HTTP_400_BAD_REQUEST)
        if len(word) > 255:
            return Response({'word': ['Ensure this field has no more than 255 characters.']},
                            status=HTTP_400_BAD_REQUEST)
        if not target_lang or len(target_lang) > 10:
            return Response({'target_lang': ['Invalid language code.']},
                            status=HTTP_400_BAD_REQUEST)
        try:
            client = get_translate_client()
            result = client.translate_text(word, target_language=target_lang)
            translation = result['translatedText']
            search_result = {
                'word': word,
                'translation': translation,
                'target_lang': target_lang,
            }
            if request.user.is_authenticated:
                SearchedWord.objects.create(
                    user=request.user,
                    content=word,
                    result=search_result,
                )
            return Response(search_result)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'detail': f'Translation service error: {exc}'}, status=HTTP_503_SERVICE_UNAVAILABLE)


class SearchHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        searches = SearchedWord.objects.filter(user=request.user)
        return Response({
            'searches': [
                {
                    'id': search.id,
                    'word': search.content,
                    'result': search.result,
                    'created_at': search.created_at.isoformat(),
                }
                for search in searches
            ]
        })

