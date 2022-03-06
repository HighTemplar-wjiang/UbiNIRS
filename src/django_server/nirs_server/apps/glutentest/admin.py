import pytz
from datetime import datetime
from django.contrib import admin
from django.conf import settings
from .models import Wrap, GlutenTestLog


# Register your nirs_models here.
class WrapAdmin(admin.ModelAdmin):
    list_display = ("id", "brand", "product_name", "label_language", "gluten_free_flag")

    class Meta:
        model = Wrap


class GlutenTestLogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in GlutenTestLog._meta.get_fields()
                    if field.name not in ("inspected_time", "scanned_time", "feedback_time", "started_time")] + [
        "get_started_timestamp", "get_inspected_timestamp", "get_scanned_timestamp", "get_feedback_timestamp",
        ]

    class Meta:
        model = GlutenTestLog

    def get_started_timestamp(self, obj):
        return datetime.timestamp(obj.started_time)
    get_started_timestamp.short_description = "Started timestamp"
    get_started_timestamp.admin_order_field = "started_time"

    def get_inspected_timestamp(self, obj):
        if obj.inspected_time is not None:
            return datetime.timestamp(obj.inspected_time)
    get_inspected_timestamp.short_description = "Inspected timestamp"
    get_inspected_timestamp.admin_order_field = "inspected_time"

    def get_scanned_timestamp(self, obj):
        if obj.scanned_time is not None:
            return datetime.timestamp(obj.scanned_time)
    get_scanned_timestamp.short_description = "Scanned timestamp"
    get_scanned_timestamp.admin_order_field = "scanned_time"

    def get_feedback_timestamp(self, obj):
        if obj.feedback_time is not None:
            return datetime.timestamp(obj.feedback_time)
    get_feedback_timestamp.short_description = "Feedback timestamp"
    get_feedback_timestamp.admin_order_field = "feedback_time"

    def get_local_time(self, obj):
        return obj.started_time.astimezone(pytz.timezone(settings.DISPLAY_TIME_ZONE)).strftime("%Y-%b-%d %H:%M:%S.%f")
    get_local_time.short_description = "Local time ({})".format(settings.DISPLAY_TIME_ZONE)
    get_local_time.admin_order_field = "started_time"

    # def get_label_language(self, obj):
    #     return obj.sample.label_language
    # get_label_language.short_description = "Label language"
    #
    # def get_ground_truth(self, obj):
    #     return "Gluten-free" if obj.sample.gluten_free_flag else "Gluten"
    # get_ground_truth.short_description = "Ground truth"


admin.site.register(Wrap, WrapAdmin)
admin.site.register(GlutenTestLog, GlutenTestLogAdmin)
