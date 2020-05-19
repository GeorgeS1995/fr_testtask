from django.db import transaction
from rest_framework import serializers
from .models import Poll, Question, AnswerType, AnswerOptions, UserPollAnswer, UserPollQuestionAnswer


class PollSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Poll
        fields = ['id', 'name', 'start_date', 'end_date', 'description']

    def validate(self, data):
        if self.instance:
            start_date = self.instance.start_date if self.instance.start_date else data.get('start_date', None)
            end_date = self.instance.end_date if self.instance.end_date else data.get('end_date', None)
        else:
            start_date = data.get('start_date', None)
            end_date = data.get('end_date', None)
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError('End date early than start date')
        return data

    def update(self, instance, validated_data):
        if instance.start_date and validated_data.get('start_date', None):
            raise serializers.ValidationError("Can't change start date if start date exist")
        return super(PollSerializer, self).update(instance, validated_data)


class AnswerOptionsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AnswerOptions
        fields = ['id', 'text']


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    answer_type = serializers.CharField(source="answer_type.type")
    answer = AnswerOptionsSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['id', 'text', 'answer_type', 'answer']

    def validate(self, data):
        if data.get('answer_type'):
            try:
                data['answer_type'] = AnswerType.objects.get(type=data['answer_type']['type'])
            except AnswerType.DoesNotExist:
                raise serializers.ValidationError("Wrong answer_type")
            if data['answer_type'].type == 'text' and data.get('answer', None):
                raise serializers.ValidationError("Can't setup answer if answer_type is text")
        return data

    def update(self, instance, validated_data):
        answers = validated_data.pop('answer', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.answer.clear()
        if answers:
            for a in answers:
                a = AnswerOptions.objects.get_or_create(text=a['text'])
                instance.answer.add(a[0].id)
        instance.save()
        return instance

    def create(self, validated_data):
        poll = self.context['request'].parser_context['kwargs']['poll_pk']
        answers = validated_data.pop('answer', None)
        with transaction.atomic():
            q_inst = super(QuestionSerializer, self).create(validated_data)
            if answers:
                for a in answers:
                    a = AnswerOptions.objects.get_or_create(text=a['text'])
                    q_inst.answer.add(a[0].id)
                    q_inst.save()
            poll = Poll.objects.get(id=poll)
            poll.question.add(q_inst)
            poll.save()
            q_inst.save()
        return q_inst


class UserPollQuestionAnswerSerializer(serializers.HyperlinkedModelSerializer):
    question = serializers.IntegerField(source='question.id')
    answer_id = serializers.IntegerField(source='answer_id.id', required=False)

    class Meta:
        model = UserPollQuestionAnswer
        fields = ['question', 'answer', 'answer_id']


class UserPollAnswerSerializer(serializers.HyperlinkedModelSerializer):
    poll = serializers.CharField(source="poll.id")
    answers = UserPollQuestionAnswerSerializer(many=True)

    class Meta:
        model = UserPollAnswer
        fields = ['user_id', 'poll', 'answers']

    def validate(self, data):
        data['poll'] = Poll.objects.get(id=data['poll']['id'])
        cur_poll_q = Question.objects.filter(isdelete=False, poll=data['poll'])
        cur_poll_q = {q.id: q for q in cur_poll_q}
        for vq in data['answers']:
            if vq['question']['id'] not in cur_poll_q.keys():
                raise serializers.ValidationError(f"Question id:{vq['question']['id']} not in poll id:"
                                                  f" {data['poll'].id}")
            question_answer_type = cur_poll_q[vq['question']['id']].answer_type.type
            if question_answer_type == 'text' and not vq.get('answer'):
                raise serializers.ValidationError(f"Question id:{vq['question']['id']} type text requires answer field")
            if question_answer_type in ['choise', 'choise_multi'] and not vq.get('answer_id'):
                raise serializers.ValidationError(f"Question id:{vq['question']['id']} type {question_answer_type}"
                                                  f" requires answer_id field")
            if vq.get('answer_id'):
                allowed_answer = {a.id:a for a in cur_poll_q[vq['question']['id']].answer.all()}
                if vq['answer_id']['id'] not in allowed_answer.keys():
                    raise serializers.ValidationError(f"Answer id:{vq['answer_id']['id']}, not allowed for question "
                                                      f"id:{vq['question']['id']}")
                vq['answer_id'] = AnswerOptions.objects.get(id=vq['answer_id']['id'])
            vq['question'] = cur_poll_q[vq['question']['id']]
        return data

    def create(self, validated_data):
        answers = validated_data['answers']
        up_inst = UserPollAnswer.objects.create(**{'user_id': validated_data['user_id'],'poll': validated_data['poll']})
        with transaction.atomic():
            for a in answers:
                q = a['question']
                first_answer = UserPollQuestionAnswer.objects.filter(user_poll=up_inst, question=q)
                if q.answer_type.type in ['text', 'choise'] and first_answer:
                    raise serializers.ValidationError("Multiple answers are possible only to choise_multi question")
                a = UserPollQuestionAnswer.objects.create(user_poll=up_inst, **a)
                a.save()
            up_inst.save()
        return up_inst


