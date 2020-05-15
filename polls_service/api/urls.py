from django.urls import path, include
from rest_framework_nested import routers
from .views import PollViewSet, QuestionViewSet, UserPollAnswerViewSet

api_v1 = routers.DefaultRouter()
api_v1.register('poll', PollViewSet)
api_v1.register('answer', UserPollAnswerViewSet, basename='answer')
question_router = routers.NestedDefaultRouter(api_v1, 'poll', lookup='poll')
question_router.register('question', QuestionViewSet, basename='poll-question')
urlpatterns = [
    path('v1/', include(api_v1.urls)),
    path('v1/', include(question_router.urls)),
    path('auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]