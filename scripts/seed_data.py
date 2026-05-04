import uuid
import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
def seed():
    from orgs.models import Organization, Workspace, WorkspaceMember
    from project.models import Project, ProjectMember, ProjectBoard, BoardColumn, Sprint, Release, ProjectType, ProjectVisibility, ProjectStatus, BoardType, BoardViewMode, RoleName, SprintStatus
    from tickets.models import Ticket, TicketType, TicketPriority, TicketStatus
    
    User = get_user_model()
    print("Starting seeding process...")
    
    # 1. Get or Create Main User
    admin_user = User.objects.filter(username='hassine').first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin', 'admin@agileflow.com', 'admin123')
    
    dev_users = User.objects.exclude(id=admin_user.id)[:4]
    
    # 2. Organizations
    org1, _ = Organization.objects.get_or_create(name="NextGen Technologies", defaults={'logo_url': 'https://api.dicebear.com/7.x/initials/svg?seed=NT'})
    org2, _ = Organization.objects.get_or_create(name="Creative Digital Agency", defaults={'logo_url': 'https://api.dicebear.com/7.x/initials/svg?seed=CDA'})
    
    # 3. Workspaces
    ws1, _ = Workspace.objects.get_or_create(organization=org1, name="Engineering Core")
    ws2, _ = Workspace.objects.get_or_create(organization=org1, name="Product Management")
    ws3, _ = Workspace.objects.get_or_create(organization=org2, name="Design Studio")
    
    # 4. Workspace Members
    for ws in [ws1, ws2, ws3]:
        WorkspaceMember.objects.get_or_create(workspace=ws, user=admin_user, defaults={'role': 'Owner'})
        for dev in dev_users:
            WorkspaceMember.objects.get_or_create(workspace=ws, user=dev, defaults={'role': 'Member'})
            
    # 5. Projects
    projects_to_create = [
        ("AgileFlow Enterprise", "Complete rebuild of our main product dashboard.", ws1, ProjectType.SOFTWARE),
        ("AI Market Bot", "Predictive analytics for marketing campaigns.", ws2, ProjectType.SOFTWARE),
        ("Mobile App v3", "iOS and Android native collaboration tools.", ws3, ProjectType.SOFTWARE),
        ("Internal Training", "Onboarding materials for new hires.", ws2, ProjectType.BUSINESS),
    ]
    
    for name, desc, ws, ptype in projects_to_create:
        proj, created = Project.objects.get_or_create(
            workspace=ws, 
            name=name, 
            defaults={
                'description': desc,
                'type': ptype,
                'visibility': ProjectVisibility.INTERNAL,
                'status': ProjectStatus.ACTIVE
            }
        )
        
        # Project Members
        ProjectMember.objects.get_or_create(project=proj, user=admin_user, defaults={'role': RoleName.ADMIN})
        for i, dev in enumerate(dev_users):
            role = RoleName.DEVELOPPEUR if i % 2 == 0 else RoleName.OBSERVATEUR
            ProjectMember.objects.get_or_create(project=proj, user=dev, defaults={'role': role})
            
        # 6. Board & Columns
        board, _ = ProjectBoard.objects.get_or_create(
            project=proj,
            defaults={'board_type': BoardType.SCRUM, 'view_mode': BoardViewMode.BOARD}
        )
        
        cols = [
            ("Backlog", 0, False),
            ("To Do", 1, False),
            ("In Progress", 2, False),
            ("Code Review", 3, False),
            ("Done", 4, True),
        ]
        columns = []
        for cname, pos, is_done in cols:
            col, _ = BoardColumn.objects.get_or_create(board=board, name=cname, defaults={'position': pos, 'is_done_column': is_done})
            columns.append(col)
            
        # 7. Sprints
        sprint, _ = Sprint.objects.get_or_create(
            board=board,
            name="Sprint 1 - Foundation",
            defaults={
                'goal': "Establish core database schema and auth.",
                'start_date': timezone.now().date(),
                'end_date': (timezone.now() + datetime.timedelta(days=14)).date(),
                'status': SprintStatus.ACTIVE
            }
        )
        
        # 8. Tickets
        ticket_data = [
            ("Initial Architecture", "Design the overall system architecture.", TicketType.EPIC, TicketPriority.CRITICAL, TicketStatus.DONE, columns[4], 5),
            ("Auth Implementation", "JWT-based authentication using cookies.", TicketType.STORY, TicketPriority.HIGH, TicketStatus.IN_PROGRESS, columns[2], 8),
            ("Kanban Board UI", "Build a drag-and-drop board for tickets.", TicketType.FEATURE, TicketPriority.MEDIUM, TicketStatus.TODO, columns[1], 13),
            ("Security Audit", "Review access control for chat channels.", TicketType.BUG, TicketPriority.CRITICAL, TicketStatus.TODO, columns[1], 3),
            ("Database Migration", "Migrate from SQLite to PostgreSQL.", TicketType.TASK, TicketPriority.LOW, TicketStatus.DONE, columns[4], 2),
        ]
        
        for title, desc, ttype, prio, status, col, pts in ticket_data:
            Ticket.objects.get_or_create(
                project=proj,
                title=title,
                defaults={
                    'description_markdown': desc,
                    'type': ttype,
                    'priority': prio,
                    'status': status,
                    'current_column': col,
                    'sprint': sprint,
                    'estimate_story_points': pts
                }
            )

        # 9. Releases
        Release.objects.get_or_create(
            project=proj,
            tag="v1.0.0-alpha",
            defaults={
                'name': "Alpha Launch",
                'description': "First stable release for internal testing.",
                'status': 'released',
                'target_date': timezone.now().date()
            }
        )

    print("Seeding complete! Admin user: hassine")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    seed()
