import datetime
from .serializers import QuestionSerializer, UserPollAnswerSerializer
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from oauth2_provider.models import AccessToken, Application
from django.utils import timezone
from .models import Poll, Question, AnswerOptions, AnswerType, UserPollAnswer
from rest_framework.reverse import reverse
from rest_framework import status

today = datetime.datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")


# Create your tests here.
class ApiUserTestClient(APITestCase):
    """
    Helper base class for API test
    """

    client = APIClient()

    @classmethod
    def setUpTestData(cls):
        users_param = {
            "username": 'test@test.com',
            "email": 'test@test.com',
            "is_active": True,
        }

        cls.user = User.objects.create(**users_param)
        cls.user.save()

        cls.application = Application.objects.create(
            name="Test Application",
            redirect_uris="http://localhost http://example.com http://example.org",
            user=cls.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )

        cls.access_token = AccessToken.objects.create(
            user=cls.user,
            scope="read write",
            expires=timezone.now() + timezone.timedelta(seconds=300),
            token="secret-access-token-key",
            application=cls.application
        )
        cls.access_token.save()
        cls.application.save()

        poll = Poll.objects.create(name='test_poll',
                                   start_date=yesterday,
                                   end_date=tomorrow,
                                   description='test')

        past_poll = Poll.objects.create(name='test_past_poll',
                                        start_date=yesterday,
                                        end_date=yesterday,
                                        description='test')
        past_poll.save()
        question_text = Question.objects.create(text='question with text answer',
                                                answer_type=AnswerType.objects.get(id=1))
        question_text.save()
        question_choise = Question.objects.create(text='question with single choise',
                                                  answer_type=AnswerType.objects.get(id=2))
        question_multi_choise = Question.objects.create(text='question with multi choise',
                                                        answer_type=AnswerType.objects.get(id=3))
        answers = ['choise1', 'choise2']
        add = True
        for a in answers:
            a = AnswerOptions.objects.create(text=a)
            a.save()
            if add:
                question_choise.answer.add(a)
                question_choise.save()
            question_multi_choise.answer.add(a)
            question_multi_choise.save()

        poll.question.add(question_text)
        poll.question.add(question_choise)
        poll.question.add(question_multi_choise)
        poll.save()

        lonely_question = Question.objects.create(text='lonely question without poll',
                                                  answer_type=AnswerType.objects.get(id=1))
        lonely_question.save()

    def tearDown(self):
        self.logout()

    def login(self):
        self.client.credentials(Authorization='Bearer {}'.format(self.access_token.token))

    def logout(self):
        self.token = None


class PollViewSetTestCase(ApiUserTestClient):

    def setUp(self):
        self.get_poll_result = [{
            'id': 1,
            'name': 'test_poll',
            'start_date': yesterday,
            'end_date': tomorrow,
            'description': 'test'
        }]

        self.create_poll_input = {
            'name': 'test_poll_2',
            'start_date': yesterday,
            'end_date': tomorrow,
            'description': 'test'
        }

        self.create_poll_output = {
            'id': 3,
            'name': 'test_poll_2',
            'start_date': yesterday,
            'end_date': tomorrow,
            'description': 'test'
        }

        self.end_before_start_input = {
            'name': 'test_poll_2',
            'start_date': tomorrow,
            'end_date': yesterday,
            'description': 'test'
        }

        self.end_before_start_output = {
            "non_field_errors": [
                "End date early than start date"
            ]
        }

        self.change_start_date_input = {
            'start_date': today,
        }
        self.change_start_date_error = [
            "Can't change start date if start date exist"
        ]

    def test_auth_required(self):
        r = self.client.post(reverse('poll-list'))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.put(reverse('poll-detail', args=(1,)))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.patch(reverse('poll-detail', args=(1,)))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.delete(reverse('poll-detail', args=(1,)))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_poll(self):
        r = self.client.get(reverse('poll-list'))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['results'], self.get_poll_result)

    def test_create_poll(self):
        self.login()
        r = self.client.post(reverse('poll-list'), self.create_poll_input)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data, self.create_poll_output)
        db = Poll.objects.get(id=self.create_poll_output['id'])
        for k, v in self.create_poll_output.items():
            db_data = getattr(db, k)
            if type(db_data) == datetime.date:
                db_data = db_data.strftime("%Y-%m-%d")
            self.assertEqual(db_data, v)

    def test_end_before_start(self):
        self.login()
        r = self.client.post(reverse('poll-list'), self.end_before_start_input)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.end_before_start_output)

    def test_change_start_date(self):
        self.login()
        r = self.client.patch((reverse('poll-detail', args=(1,))), self.change_start_date_input)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.change_start_date_error)


class QuestionViewSetTestCase(ApiUserTestClient):

    def setUp(self) -> None:
        self.get_question_output = [
            {"id": 1, "text": "question with text answer", "answer_type": "text", "answer": []},
            {"id": 2, "text": "question with single choise", "answer_type": "choise", "answer": [
                {"id": 1, "text": "choise1"}, {"id": 2, "text": "choise2"}]},
            {"id": 3, "text": "question with multi choise", "answer_type": "choise_multi", "answer":
                [{"id": 1, "text": "choise1"}, {"id": 2, "text": "choise2"}]}]

        self.create_text_question = {
            "text": "new_question with text answer",
            "answer_type": "text"
        }

        self.create_text_question_output = {
            'id': 5,
            "text": "new_question with text answer",
            "answer_type": "text",
            "answer": []
        }

        self.create_choise_question = {
            "text": "new question with single choise",
            "answer_type": "choise",
            "answer": [
                {"text": "choise1"},
                {"text": "choise3"}
            ]
        }

        self.create_choise_question_output = {
            "id": 5,
            "text": "new question with single choise",
            "answer_type": "choise",
            "answer": [
                {"id": 1, "text": "choise1"},
                {"id": 3, "text": "choise3"}
            ]
        }

        self.edite_choise_question = {
            "answer": [
                {"id": 1, "text": "choise1"},
                {"id": 3, "text": "choise3"}
            ]
        }

        self.edite_choise_question_output = {"id": 2,
                                             "text": "question with single choise",
                                             "answer_type": "choise",
                                             "answer": [
                                                 {"id": 1,
                                                  "text": "choise1"},
                                                 {"id": 3,
                                                  "text": "choise3"}
                                             ]}

        self.text_question_with_answer_error_input = {
            "text": "new question with single choise",
            "answer_type": "text",
            "answer": [
                {"text": "choise1"},
                {"text": "choise3"}
            ]
        }

        self.text_question_with_answer_error = {
            "non_field_errors": [
                "Can't setup answer if answer_type is text"
            ]
        }

        self.wrong_answer_type = {
            "text": "new question with single choise",
            "answer_type": "wrong_answer_type",
            "answer": [
                {"text": "choise1"},
                {"text": "choise3"}
            ]
        }

        self.wrong_answer_error = {
            "non_field_errors": [
                "Wrong answer_type"
            ]
        }

    def test_auth_required(self):
        r = self.client.post(reverse('poll-question-list', args=(1,)))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.put(reverse('poll-question-detail', args=(1, 1)))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.patch(reverse('poll-question-detail', args=(1, 1)))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.delete(reverse('poll-question-detail', args=(1, 1)))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_question(self):
        r = self.client.get(reverse('poll-question-list', args=(1,)))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['results'], self.get_question_output)

    def test_create_text_question(self):
        self.login()
        r = self.client.post(reverse('poll-question-list', args=(1,)), self.create_text_question)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data, self.create_text_question_output)
        db = Question.objects.get(id=5)
        db_serialized = QuestionSerializer(db).data
        self.assertEqual(db_serialized, self.create_text_question_output)

    def test_create_choise_question(self):
        self.login()
        r = self.client.post(reverse('poll-question-list', args=(1,)),
                             data=self.create_choise_question,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data, self.create_choise_question_output)
        db = Question.objects.get(id=5)
        db_serialized = QuestionSerializer(db).data
        self.assertEqual(db_serialized, self.create_choise_question_output)

    def test_edite_question(self):
        self.login()
        r = self.client.patch(reverse('poll-question-detail', args=(1, 2)),
                              data=self.edite_choise_question,
                              format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data, self.edite_choise_question_output)

    def test_text_question_with_answer_error(self):
        self.login()
        r = self.client.post(reverse('poll-question-list', args=(1,)),
                             data=self.text_question_with_answer_error_input,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.text_question_with_answer_error)

    def test_wrong_answer_type(self):
        self.login()
        r = self.client.post(reverse('poll-question-list', args=(1,)),
                             data=self.wrong_answer_type,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.wrong_answer_error)


class UserPollAnswerViewSetTestCase(ApiUserTestClient):

    def setUp(self) -> None:
        self.poll_answer = {
            "user_id": 1,
            "poll": 1,
            "answers": [
                {"question": 1,
                 "answer": "text_answer"
                 },
                {"question": 2,
                 "answer_id": 1
                 },
                {"question": 3,
                 "answer_id": 1
                 },
                {"question": 3,
                 "answer_id": 2
                 },
            ]
        }

        self.poll_answer_output = {
            "user_id": 1,
            "poll": "1",
            "answers": [
                {"question": 1, "answer": "text_answer"},
                {"question": 2, "answer": "", "answer_id": 1},
                {"question": 3, "answer": "", "answer_id": 1},
                {"question": 3, "answer": "", "answer_id": 2}
            ]
        }

        self.poll_answer_wrong_question = {
            "user_id": 1,
            "poll": 1,
            "answers": [
                {"question": 4, "answer": "text_answer"},
            ]
        }

        self.poll_answer_wrong_question_error = {
            "non_field_errors": [
                "Question id:4 not in poll id: 1"
            ]
        }

        self.answer_text_question_without_answer = {
            "user_id": 1,
            "poll": "1",
            "answers": [
                {"question": 1}
            ]
        }

        self.answer_text_question_without_answer_output = {
            "non_field_errors": [
                "Question id:1 type text requires answer field"
            ]
        }

        self.answer_choise_question_without_answer = {
            "user_id": 1,
            "poll": "1",
            "answers": [
                {"question": 2}
            ]
        }

        self.answer_choise_question_without_answer_output = {
            "non_field_errors": [
                "Question id:2 type choise requires answer_id field"
            ]
        }

        self.answer_choise_question_wrong_answer = {
            "user_id": 1,
            "poll": "1",
            "answers": [
                {"question": 2, "answer_id": 3}
            ]
        }

        self.answer_choise_question_multiple_answer = {
            "user_id": 1,
            "poll": "1",
            "answers": [
                {"question": 2, "answer_id": 1},
                {"question": 2, "answer_id": 2}
            ]
        }

        self.answer_multichoise_error = [
                "Multiple answers are possible only to choise_multi question"
            ]

        self.answer_choise_question_wrong_answer_output = {
            "non_field_errors": [
                "Answer id:3, not allowed for question id:2"
            ]
        }

        self.user_answer = {"count": 1,
                            "next": None,
                            "previous": None,
                            "results": [
                                {"user_id": 1,
                                 "poll": "1",
                                 "answers": [
                                     {"question": 1, "answer": "text_answer"},
                                     {"question": 2, "answer": "", "answer_id": 1},
                                     {"question": 3, "answer": "", "answer_id": 1},
                                     {"question": 3, "answer": "", "answer_id": 2}
                                 ]}
                            ]}

        self.empty_user_id_error = [
            "Empty param user_id"
        ]

    def test_allowed_method(self):
        response = self.client.post(reverse('answer-list'),
                                    data=self.poll_answer,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(reverse('answer-list'), {'user_id': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(reverse('answer-list'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.patch(reverse('answer-list'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.delete(reverse('answer-list'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_answer_poll(self):
        r = self.client.post(reverse('answer-list'),
                             data=self.poll_answer,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data, self.poll_answer_output)
        db = UserPollAnswer.objects.get(id=1)
        db_serialized = UserPollAnswerSerializer(db).data
        self.assertEqual(db_serialized, self.poll_answer_output)

    def test_answer_to_wrong_question(self):
        r = self.client.post(reverse('answer-list'),
                             data=self.poll_answer_wrong_question,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.poll_answer_wrong_question_error)

    def test_answer_text_question_without_answer(self):
        r = self.client.post(reverse('answer-list'),
                             data=self.answer_text_question_without_answer,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.answer_text_question_without_answer_output)

    def test_answer_choise_question_without_answer(self):
        r = self.client.post(reverse('answer-list'),
                             data=self.answer_choise_question_without_answer,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.answer_choise_question_without_answer_output)

    def test_answer_choise_question_wrong_answer(self):
        r = self.client.post(reverse('answer-list'),
                             data=self.answer_choise_question_wrong_answer,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.answer_choise_question_wrong_answer_output)

    def test_answer_choise_question_multiple_answer(self):
        r = self.client.post(reverse('answer-list'),
                             data=self.answer_choise_question_multiple_answer,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.answer_multichoise_error)

    def test_get_answer(self):
        r = self.client.post(reverse('answer-list'),
                             data=self.poll_answer,
                             format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.get(reverse('answer-list'), {'user_id': 1})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data, self.user_answer)

    def test_get_answer_empty_user_id(self):
        r = self.client.get(reverse('answer-list'))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, self.empty_user_id_error)
