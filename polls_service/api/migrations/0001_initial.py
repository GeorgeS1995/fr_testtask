# Generated by Django 3.0.6 on 2020-05-12 16:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnswerOptions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='AnswerType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('start_date', models.DateField(blank=True)),
                ('end_date', models.DateField(blank=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=1000)),
                ('answer', models.ManyToManyField(to='api.AnswerOptions')),
                ('answer_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.AnswerType')),
            ],
        ),
        migrations.CreateModel(
            name='UserPollAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.PositiveIntegerField()),
                ('poll', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.Poll')),
            ],
        ),
        migrations.CreateModel(
            name='UserPoolQuestionAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.CharField(blank=True, max_length=255)),
                ('answer_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.AnswerOptions')),
                ('question', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.Question')),
                ('user_poll', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.UserPollAnswer')),
            ],
        ),
        migrations.AddField(
            model_name='poll',
            name='question',
            field=models.ManyToManyField(to='api.Question'),
        ),
    ]
