import os
import time
import json
import shutil
import numpy as np
import subprocess
from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.dispatch import receiver
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.db.models.signals import pre_save, post_save, post_delete
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import User, Group
from .models import UbiNIRSApp, AppTestLog, AppSpectrumLabel, AppSpectrumFile
from nirs_server.settings import BASE_DIR, MEDIA_ROOT
# from nested_inline.admin import NestedStackedInline, NestedModelAdmin
import nested_admin


class AppFileForm(forms.ModelForm):

    file = forms.FileField(widget=forms.FileInput(attrs={"multiple": True, "required": True}))

    def __init__(self, *args, **kwargs):
        super(AppFileForm, self).__init__(*args, **kwargs)

    class Meta:
        model = AppSpectrumFile
        fields = ["file"]

    def save(self, *args, **kwargs):

        invert_data = dict([(v, k) for k, v in self.data.dict().items() if isinstance(v, str) and len(v) > 5])
        label = self.cleaned_data["label"].label
        set_prefix = "-".join(invert_data[label].split("-")[:-1])

        for key in self.files.keys():

            if not key.startswith(set_prefix):
                # Request from other sets, skip.
                continue

            file_list = self.files.getlist(key)

            self.instance.file = file_list[0]
            for file in file_list[1:]:
                print(file)
                AppSpectrumFile(
                    label=self.cleaned_data["label"],
                    file=file).save()

        return super().save(*args, **kwargs)


class AppFileInline(nested_admin.NestedStackedInline):
    """Inline upload file."""
    model = AppSpectrumFile
    form = AppFileForm
    extra = 1
    fk_name = 'label'
    exclude = ("app", )


class AppLabelInline(nested_admin.NestedStackedInline):
    """Inline label model."""
    model = AppSpectrumLabel
    extra = 1
    fk_name = 'app'
    inlines = [AppFileInline]


class UbiNIRSAppAdmin(nested_admin.NestedModelAdmin):
    """Admin model for NIRS apps."""
    exclude = ("app_name", "app_classes")
    # readonly_fields = ("displayname_to_name", "app_classes")
    # list_display = ("app_id", "get_app_name", "get_owner_name", "app_version",
    #                 "get_created_time", "get_updated_time", "app_visits")
    list_display = ("get_app_name", "get_owner_name", "app_version", "app_visits")
    inlines = [AppLabelInline]

    class Meta:
        model = UbiNIRSApp

    def get_app_name(self, obj):
        return obj.app_displayname
    get_app_name.short_description = "App Name"

    def get_created_time(self, obj):
        return obj.app_created_at
    get_created_time.short_description = "Created At (UTC)"

    def get_updated_time(self, obj):
        return obj.app_updated_at
    get_updated_time.short_description = "Updated At (UTC)"

    def get_owner_name(self, obj):
        return obj.app_owner.get_full_name()
    get_owner_name.short_description = "App Owner"

    # Modify form fields.
    def get_fieldsets(self, request, obj=None):
        fieldsets = super(UbiNIRSAppAdmin, self).get_fieldsets(request, obj)
        return fieldsets

    # After database updated, create the app folder and train the model if possible.
    @staticmethod
    @receiver(post_save, sender=UbiNIRSApp)
    def handle_post_save(instance, **kwargs):
        # Get new app name.
        new_app_name = instance.app_name

        # Execute the startapp command.
        new_app_full_path = os.path.join(BASE_DIR, "apps/{}".format(new_app_name))
        # Create directory if not exist.
        if UbiNIRSApp.objects.filter(pk=instance.app_id).exists():
            # os.popen("mkdir {}".format(new_app_full_path))
            subprocess.Popen("mkdir {}".format(new_app_full_path).split(" ")).wait()
            # startapp
            subprocess.Popen(["bash", os.path.join(BASE_DIR, "./start_new_app.sh"),
                              new_app_name,
                              new_app_full_path,
                              os.path.join(BASE_DIR, "dashboard/templates/app")]).wait()
            # subprocess.Popen("python manage.py startapp {} {} --template={}".format(
            #     new_app_name,
            #     new_app_full_path,
            #     os.path.join(BASE_DIR, "dashboard/templates/app")).split(" ")).wait()
            # result = os.popen("python manage.py startapp {} {} --template={}".format(
            #     new_app_name,
            #     new_app_full_path,
            #     os.path.join(BASE_DIR, "dashboard/templates/app")))
            # print(result)

        else:
            # TODO: app exits.
            pass

        # TODO: Use a better way to inform restart, e.g., using gunicorn.
        time.sleep(5)
        # os.system(
        #     r"systemctl status gunicorn |  sed -n 's/.*Main PID: \(.*\)$/\1/g p' | cut -f1 -d' ' | xargs kill -HUP")
        # os.system("touch {}".format(os.path.join(BASE_DIR, "./urls.py")))
        os.system("echo "" >> {}".format(os.path.join(BASE_DIR, "./nirs_server/urls.py")))

    @staticmethod
    @receiver(pre_save, sender=UbiNIRSApp)
    def handle_pre_save(instance, **kwargs):
        pass

    @receiver(post_delete)
    def post_delete_app(sender, instance, **kwargs):
        """Move app directory to trash bin after deleting it."""

        # Check model type.
        if isinstance(instance, UbiNIRSApp):
            deleted_app_name = instance.app_name
            deleted_app_full_path = os.path.join(BASE_DIR, "./apps/" + deleted_app_name)
            trashbin_full_path = os.path.join(BASE_DIR,
                                              "./trashbin/{}_{}".format(deleted_app_name, int(time.time() * 1000)))

            # Move to trash bin and overwrite existing folders.
            try:
                shutil.move(deleted_app_full_path, trashbin_full_path, copy_function=shutil.copytree)
            except FileNotFoundError as fnfe:
                pass
        elif isinstance(instance, AppSpectrumFile):
            # deleted_file_name = os.path.basename(instance.file.file.name)
            pass

    # Change App form.
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):

        return super().changeform_view(request, object_id, form_url, extra_context)

    # Show the stat. in days.
    def changelist_view(self, request, extra_context=None):

        # ChangeList = self.get_changelist(request)
        cl = ChangeList(request, self.model, self.list_display,
                        self.list_display_links, self.list_filter, self.date_hierarchy,
                        self.search_fields, self.list_select_related, self.list_per_page,
                        self.list_max_show_all, self.list_editable, self, self.sortable_by)

        chart_data = cl.get_queryset(request).values()

        # Serialize and attach data to Chart.
        as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
        extra_context = extra_context or {"chart_data": as_json}

        # Render.
        return super().changelist_view(request, extra_context=extra_context)


class AppTestLogAdmin(admin.ModelAdmin):
    list_display = ("test_transaction_number", "get_app_name", "test_device_id", "test_result",
                    "test_created_at", "test_feedback")
    list_filter = ("test_feedback", "app__app_displayname", "test_result")
    readonly_fields = ("test_transaction_number", "test_result", "get_app_name",
                       "test_device_id", "test_feedback", "test_filename", "test_created_at")

    class Meta:
        model = AppTestLog

    def get_app_name(self, obj):
        return obj.app.app_displayname
    get_app_name.admin_order_field = "app"
    get_app_name.short_description = "App Name"

    def has_add_permission(self, request, obj=None):
        return False

    # Show the stat. in days.
    def changelist_view(self, request, extra_context=None):

        # ChangeList = self.get_changelist(request)
        cl = ChangeList(request, self.model, self.list_display,
                        self.list_display_links, self.list_filter, self.date_hierarchy,
                        self.search_fields, self.list_select_related, self.list_per_page,
                        self.list_max_show_all, self.list_editable, self, self.sortable_by)

        chart_data = (
            cl.get_queryset(request).annotate(date=TruncDay("test_created_at"))
            .values("date")
            .annotate(y=Count("test_transaction_number"))
            .order_by("-date")
        )

        # Serialize and attach data to Chart.
        as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
        extra_context = extra_context or {"chart_data": as_json}

        # Render.
        return super().changelist_view(request, extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):

        # Construct the path to log data.
        test_log = AppTestLog.objects.get(pk=object_id)
        app_name = test_log.app.app_name
        log_filename = test_log.test_filename
        full_log_path = os.path.join(BASE_DIR, "./apps/{}/nirs_models/data/test/{}".format(app_name, log_filename))

        # Read data.
        chart_data = {}
        if os.path.exists(full_log_path):
            data = np.loadtxt(full_log_path, delimiter=",")
            chart_data["wavelength"] = data[:, 0].tolist()
            chart_data["intensity_spectrum"] = data[:, 1].tolist()
            chart_data["reference_spectrum"] = data[:, 2].tolist()
            chart_data["reflectance"] = (data[:, 1] / data[:, 2]).tolist()
            chart_data["absorbance"] = np.log10(data[:, 2] / data[:, 1]).tolist()
        as_json = json.dumps(chart_data, cls=DjangoJSONEncoder)
        extra_context = extra_context or {"chart_data": as_json}

        return super().changeform_view(request, object_id=object_id, form_url=form_url, extra_context=extra_context)


# Register your models here.
# admin.site.unregister(User)
# admin.site.unregister(Group)
admin.site.register(UbiNIRSApp, UbiNIRSAppAdmin)
admin.site.register(AppTestLog, AppTestLogAdmin)

# Customize site.
admin.site.site_header = "UbiNIRS App Dashboard"
admin.site.site_title = "UbiNIRS Admin Dashboard"
admin.site.index_title = "Welcome to UbiNIRS Dashboard"
