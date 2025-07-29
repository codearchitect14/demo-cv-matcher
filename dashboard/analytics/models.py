from django.db import models

class Candidate(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    domain = models.CharField(max_length=100)
    # Add other fields as needed

    class Meta:
        managed = False  # Don't let Django create/drop this table
        db_table = 'candidates'

class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=100)
    domain = models.CharField(max_length=100)
    # Add other fields as needed

    class Meta:
        managed = False
        db_table = 'jobs'

class Application(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job, on_delete=models.DO_NOTHING, db_column='job_id')
    candidate = models.ForeignKey(Candidate, on_delete=models.DO_NOTHING, db_column='candidate_id')
    status = models.CharField(max_length=20)
    # Add other fields as needed

    class Meta:
        managed = False
        db_table = 'applications'

class InteractionLog(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Candidate, on_delete=models.DO_NOTHING, db_column='user_id')
    job = models.ForeignKey(Job, on_delete=models.DO_NOTHING, db_column='job_id')
    interaction_type = models.CharField(max_length=20)
    timestamp = models.DateTimeField()
    # Add other fields as needed

    class Meta:
        managed = False
        db_table = 'interaction_log'