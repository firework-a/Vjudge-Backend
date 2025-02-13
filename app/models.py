from tortoise import fields, models
from datetime import datetime

class User(models.Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=128, unique=True)
    password_hash = fields.CharField(max_length=128)
    nick_name = fields.CharField(max_length=50, null=True)
    phone = fields.CharField(max_length=20, null=True)
    solved = fields.IntField(default=0)
    is_admin = fields.BooleanField(default=False)
    avatar = fields.CharField(max_length=128, default="default.png")
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

class Notice(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=128)
    content = fields.TextField()
    time = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notices"

class Source(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)

    class Meta:
        table = "sources"

class Tag(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)

    class Meta:
        table = "tags"

class Question(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=128)
    difficulty = fields.IntField()
    source = fields.ForeignKeyField('models.Source', related_name='questions')
    tags = fields.ManyToManyField('models.Tag', related_name='questions', through='question_tags')
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "questions"
