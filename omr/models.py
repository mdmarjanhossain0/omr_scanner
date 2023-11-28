from django.db import models

from datetime import datetime

class OMRExam(models.Model):
    exam_name = models.CharField(max_length=255)
    answers = models.TextField(
        null=False, blank=False
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="created_at"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated_at")

    def save(self, *args, **kwargs):
        super(OMRExam, self).save(*args, **kwargs)

def omr_upload_location(instance, filename, **kwargs):
    file_path = f"omr_sheet/{datetime.now().timestamp()}-{filename}"
    return file_path

class ScannedPaper(models.Model):
    exam = models.ForeignKey(OMRExam, on_delete=models.SET_NULL, null=True, blank=True)
    omr_sheet = models.ImageField(upload_to=omr_upload_location)
    correct = models.IntegerField(default=0)
    wrong = models.IntegerField(default=0)
    blank = models.IntegerField(default=0)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="created_at"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated_at")
