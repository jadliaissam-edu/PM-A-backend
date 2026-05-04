from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from accounts.authentication import JWTAuthentication
from tickets.models import Ticket
from tickets.serializer import TicketSerializer
from django.db.models import Q
from django.db import connection

# Try to import postgres specific search
try:
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    HAS_POSTGRES_SEARCH = True
except ImportError:
    HAS_POSTGRES_SEARCH = False

class GlobalSearchView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({"results": []})

        # Base queryset: only tickets in projects where user is a member
        # (Alternatively, all tickets if user is superuser, but let's stick to memberships)
        from project.models import ProjectMember
        user_project_ids = ProjectMember.objects.filter(user=request.user).values_list('project_id', flat=True)
        
        queryset = Ticket.objects.filter(project_id__in=user_project_ids)

        if HAS_POSTGRES_SEARCH and connection.vendor == 'postgresql':
            # Use Postgres Full-Text Search
            vector = SearchVector('title', weight='A') + SearchVector('description_markdown', weight='B')
            search_query = SearchQuery(query)
            queryset = queryset.annotate(
                rank=SearchRank(vector, search_query)
            ).filter(rank__gte=0.1).order_by('-rank')
        else:
            # Fallback for SQLite or if postgres not configured
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description_markdown__icontains=query)
            ).order_by('-created_at')

        # Limit results
        results = queryset[:50]
        serializer = TicketSerializer(results, many=True)
        
        return Response({
            "query": query,
            "engine": "postgres" if (HAS_POSTGRES_SEARCH and connection.vendor == 'postgresql') else "basic",
            "results": serializer.data
        })
