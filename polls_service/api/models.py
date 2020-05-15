from django.db import models


# Create your models here.

class AnswerType(models.Model):
    type = models.CharField(max_length=255)
    isdelete = models.BooleanField(default=False)


class AnswerOptions(models.Model):
    text = models.CharField(max_length=255)
    isdelete = models.BooleanField(default=False)


class Question(models.Model):
    text = models.CharField(max_length=1000)
    answer_type = models.ForeignKey(AnswerType, on_delete=models.SET_NULL, null=True)
    answer = models.ManyToManyField(AnswerOptions, blank=True)
    isdelete = models.BooleanField(default=False)


class Poll(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    question = models.ManyToManyField(Question, blank=True)
    isdelete = models.BooleanField(default=False)


class UserPollAnswer(models.Model):
    user_id = models.PositiveIntegerField()
    poll = models.ForeignKey(Poll, on_delete=models.SET_NULL, null=True, blank=False)
    isdelete = models.BooleanField(default=False)


class UserPollQuestionAnswer(models.Model):
    user_poll = models.ForeignKey(UserPollAnswer, on_delete=models.SET_NULL, null=True, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)
    answer = models.CharField(max_length=255, blank=True)
    answer_id = models.ForeignKey(AnswerOptions, on_delete=models.SET_NULL, blank=True, null=True)
    isdelete = models.BooleanField(default=False)
