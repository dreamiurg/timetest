from django.db import models
from django import forms

class Comment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()
    

class CommentForm(forms.Form):
    comment = forms.CharField(max_length=100, label="Have anything to say?", widget=forms.Textarea)

