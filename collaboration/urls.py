from rest_framework.urls import path

from collaboration.views import CommentDeleteView , CommentListView, CommentCreateView, CommentupdateView, ReactionDeleteView, ReactionListView, ReactionCreateView

urlpatterns = [
    path('tickets/<uuid:ticketId>/comments/', CommentListView.as_view()),
    path('tickets/<uuid:ticketId>/comments/create/', CommentCreateView.as_view()),
    path('comments/<uuid:id>/', CommentupdateView.as_view()),
    path('comments/<uuid:id>/delete/', CommentDeleteView.as_view()),
    path('comments/<uuid:commentId>/reactions/', ReactionListView.as_view()),
    path('comments/<uuid:commentId>/reactions/add/', ReactionCreateView.as_view()),
    path('comments/<uuid:commentId>/reactions/<uuid:id>/', ReactionDeleteView.as_view()),
    ]   