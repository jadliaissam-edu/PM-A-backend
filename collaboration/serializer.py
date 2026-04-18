from rest_framework import serializers
from .models import Comment, Reaction


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'ticket',
            'author',
            'author_name',
            'body',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['id', 'comment', 'user', 'type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

