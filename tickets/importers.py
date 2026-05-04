import csv
import os
import requests
from django.core.files.storage import default_storage
from .models import Ticket, TicketImportJob, ImportStatus
from project.models import Project

def process_ticket_import_job(job_id):
    try:
        job = TicketImportJob.objects.get(id=job_id)
    except TicketImportJob.DoesNotExist:
        return

    job.status = ImportStatus.RUNNING
    job.save()

    try:
        # For simplicity, we assume the source_file_url is a path on disk if it starts with /
        # Or a remote URL if it starts with http
        if job.source_file_url.startswith('http'):
            response = requests.get(job.source_file_url)
            content = response.text
        else:
            with default_storage.open(job.source_file_url) as f:
                content = f.read().decode('utf-8')

        if job.format == 'csv':
            import_csv_tickets(job.project, content)
        elif job.format == 'markdown':
            import_markdown_tickets(job.project, content)

        job.status = ImportStatus.SUCCESS
    except Exception as e:
        print(f"Import failed: {str(e)}")
        job.status = ImportStatus.FAILED
    
    job.save()

def import_csv_tickets(project, content):
    reader = csv.DictReader(content.splitlines())
    tickets_to_create = []
    for row in reader:
        # Expected headers: title, description, type, priority
        tickets_to_create.append(Ticket(
            project=project,
            title=row.get('title', 'Imported Ticket'),
            description_markdown=row.get('description', ''),
            type=row.get('type', 'task'),
            priority=row.get('priority', 'medium'),
            status='todo'
        ))
    Ticket.objects.bulk_create(tickets_to_create)

def import_markdown_tickets(project, content):
    # Every line starting with "- [ ]" is a new ticket
    tickets_to_create = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("- [ ] "):
            title = line[6:].strip()
            if title:
                tickets_to_create.append(Ticket(
                    project=project,
                    title=title,
                    status='todo'
                ))
    Ticket.objects.bulk_create(tickets_to_create)
