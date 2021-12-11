import os
import time
import random
from django import forms
from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.contrib.auth.models import User
from nirs_server.settings import BASE_DIR


def id_generator():
    """Generate a random ID."""
    new_id = random.randint(1, 2 ** 63 - 1)
    while UbiNIRSApp.objects.filter(app_id=new_id):
        new_id = random.randint(1, 2 ** 63 - 1)

    return new_id


# App table.
class UbiNIRSApp(models.Model):
    app_id = models.IntegerField(primary_key=True, editable=False, default=id_generator)
    app_name = models.CharField(unique=True, max_length=150, editable=False, verbose_name="appname")
    app_displayname = models.CharField(default="", max_length=1024, verbose_name="App Name")
    app_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    app_description = models.TextField(default="")
    app_version = models.CharField(default="", max_length=1024)
    app_icon = models.CharField(default="", max_length=65535)
    app_thumbnail = models.CharField(default="", max_length=65535)
    app_classes = models.TextField(default="", editable=False)
    app_visits = models.IntegerField(default=0)
    app_created_at = models.DateTimeField(auto_now_add=True)
    app_updated_at = models.DateTimeField(auto_now=True)

    def get_app_name(self):
        """Convert a human readable name to a machine-friendly app name.
                e.g.: My App --> myapp
            """
        return self.app_displayname.replace(" ", "").replace("_", "").lower()

    def save(self, *args, **kwargs):
        """Generate machine-friendly app name and save."""
        self.app_name = self.get_app_name()
        super(UbiNIRSApp, self).save(args, kwargs)

    # Not overriding the __dict__ method.
    def to_dict(self):
        result = {
            "app_id": self.app_id,
            "app_displayname": self.app_displayname,
            "app_owner": User.objects.filter(pk=self.app_owner_id)[0].get_full_name(),
            "app_description": self.app_description,
            "app_version": self.app_version,
            "app_icon": self.app_icon,
            "app_thumbnail": self.app_thumbnail,
            "app_classes": self.app_classes,
        }

        return result

    def get_app_reference_path(self):
        """Get app reference folder path."""
        return os.path.join(BASE_DIR,
                            "./apps/{}/nirs_models/data/reference/".format(self.app_name))


# App test log.
class AppTestLog(models.Model):
    test_transaction_number = models.IntegerField(primary_key=True, editable=False)
    app = models.ForeignKey(UbiNIRSApp, on_delete=models.CASCADE, null=False, editable=False)
    test_result = models.CharField(default="", max_length=64, editable=False)
    test_device_id = models.CharField(max_length=64, null=True, editable=False)
    test_feedback = models.BooleanField(editable=False, default=True)
    test_filename = models.CharField(max_length=1024, editable=False)
    test_created_at = models.DateTimeField(auto_now_add=True, editable=False)
    test_note = models.TextField(default="", null=True, editable=True)


# Object categories.
class AppSpectrumLabel(models.Model):
    app = models.ForeignKey(UbiNIRSApp, on_delete=models.CASCADE, null=False, editable=True)
    label = models.CharField(max_length=1024)
    description = models.TextField(null=True, editable=True)


def get_reference_file_path(instance, filename):
    """Find the file path."""
    # Rename the file.
    filename = "{}_{}.csv".format(instance.label.label, int(time.time() * 1000))

    return os.path.join(instance.app.get_app_reference_path(), filename)


# App reference data table.
class AppSpectrumFile(models.Model):
    id = models.AutoField(primary_key=True)
    app = models.ForeignKey(UbiNIRSApp, on_delete=models.CASCADE, null=True)
    label = models.ForeignKey(AppSpectrumLabel, on_delete=models.CASCADE, null=False, editable=True)
    file = models.FileField(upload_to=get_reference_file_path,
                            max_length=100000, validators=[FileExtensionValidator(allowed_extensions=["csv"])])
    uploaded_at = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        """Save corresponding App."""
        self.app = self.label.app

        super(AppSpectrumFile, self).save(args, kwargs)

