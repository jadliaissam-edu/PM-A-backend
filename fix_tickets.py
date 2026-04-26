from project.models import BoardColumn
from tickets.models import Ticket

tickets = Ticket.objects.filter(current_column=None)
print(f"Found {tickets.count()} tickets without column")

for t in tickets:
    col = BoardColumn.objects.filter(board__project=t.project).order_by('position').first()
    if col:
        t.current_column = col
        t.save()
        print(f"Fixed ticket {t.id} ({t.title}) -> Column: {col.name}")
    else:
        print(f"Skipped ticket {t.id} ({t.title}) - No board column found for project {t.project.name}")
