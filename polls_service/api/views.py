from rest_framework import permissions, viewsets, mixins
from rest_framework.viewsets import ModelViewSet
from .models import Poll, Question, UserPollAnswer
from .serializers import PollSerializer, QuestionSerializer, UserPollAnswerSerializer
import datetime
from rest_framework import serializers

today = datetime.datetime.now().strftime("%Y-%m-%d")


# Create your views here.


class PollViewSet(ModelViewSet):
    queryset = Poll.objects.filter(isdelete=False, end_date__gt=today).order_by('id')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = PollSerializer

    def perform_destroy(self, instance):
        instance.isdelete = True
        instance.save(update_fields=['isdelete'])


class QuestionViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return Question.objects.filter(isdelete=False, poll__in=[self.kwargs['poll_pk']]).order_by('id')

    def get_serializer_context(self):
        self.request.parser_context['poll'] = self.kwargs['poll_pk']
        return super().get_serializer_context()

    def perform_destroy(self, instance):
        instance.isdelete = True
        instance.save(update_fields=['isdelete'])


class UserPollAnswerViewSet(viewsets.GenericViewSet,
                            mixins.CreateModelMixin,
                            mixins.ListModelMixin):
    serializer_class = UserPollAnswerSerializer

    def get_queryset(self):
        if not self.request.GET.get('user_id', None):
            raise serializers.ValidationError('Empty param user_id')
        return UserPollAnswer.objects.filter(isdelete=False, user_id=self.request.GET['user_id']).order_by('id')
