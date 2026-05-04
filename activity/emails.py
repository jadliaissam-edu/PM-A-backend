from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_project_invitation_email(recipient_email, inviter_name, project_name, workspace_name):
    subject = f"You've been invited to '{project_name}' on AgileFlow"
    context = {
        'inviter_name': inviter_name,
        'project_name': project_name,
        'workspace_name': workspace_name,
        'app_name': 'AgileFlow'
    }
    
    # Simple text message for now, can be expanded to HTML
    message = f"Hi,\n\n{inviter_name} has invited you to collaborate on the project '{project_name}' in the workspace '{workspace_name}'.\n\nLogin to your dashboard to get started.\n\nBest,\nThe {context['app_name']} Team"
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=True,
    )

def send_mention_notification_email(recipient_email, author_name, content_snippet, target_name, target_url):
    subject = f"{author_name} mentioned you in a comment"
    message = f"Hi,\n\n{author_name} mentioned you in a comment on '{target_name}':\n\n\"{content_snippet}\"\n\nView it here: {target_url}\n\nBest,\nThe AgileFlow Team"
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=True,
    )
