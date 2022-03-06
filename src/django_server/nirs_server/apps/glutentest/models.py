from django.db import models


class Wrap(models.Model):

    id = models.CharField(primary_key=True, max_length=100)
    brand = models.CharField(null=False, max_length=100)
    product_name = models.CharField(null=False, max_length=100)
    gluten_free_flag = models.BooleanField(null=False)
    label_language = models.CharField(max_length=100, choices=[
        ("English", "English"),
        ("Russian", "Russian"),
        ("No label", "No label")])


class GlutenTestLog(models.Model):

    transaction_num = models.IntegerField(primary_key=True, editable=False)
    participant_id = models.CharField(null=False, max_length=100)
    sample_id = models.CharField(null=False, max_length=100)
    inspection_result = models.BooleanField(null=True, max_length=100)
    scanned_result = models.CharField(null=True, max_length=100)
    visualization_method = models.CharField(null=False, max_length=100)
    probability = models.FloatField(null=True)
    trust_flag = models.BooleanField(null=True)
    session = models.CharField(null=False, max_length=100)
    started_time = models.DateTimeField(null=False)
    inspected_time = models.DateTimeField(null=True)
    scanned_time = models.DateTimeField(null=True)
    feedback_time = models.DateTimeField(null=True)
    label_language = models.CharField(null=False, max_length=100, choices=[
        ("English", "English"),
        ("Russian", "Russian"),
        ("No label", "No label")])

