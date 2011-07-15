from annoying.decorators import render_to
from datetime import datetime
from common.models import *

@render_to('home.html')
def home(request):
    comment_form = CommentForm()

    results = {'utcnow': datetime.utcnow(),
               'form': comment_form,
               }

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        
        if comment_form.is_valid() and len(comment_form.cleaned_data['comment'].strip()) > 0:
            comment = Comment()
            comment.created_at = datetime.utcnow()
            comment.comment = comment_form.cleaned_data['comment'].strip()
            comment.save()

    results['comments'] = Comment.objects.all().order_by('-created_at')

    return results