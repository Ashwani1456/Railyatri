from django.contrib import admin
from django.contrib import messages
from datetime import timedelta, date

from .models import Station, Train, Schedule, Seat_Chart, Ticket

# ───── UTIL: Admin Action for Seat Chart Generation ─────
@admin.action(description="Generate seat charts for next 7 days (by train)")
def generate_charts_from_schedules(modeladmin, request, queryset):
    today = date.today()
    created = 0
    trains = {s.train for s in queryset}

    for train in trains:
        for offset in range(7):
            target_date = today + timedelta(days=offset)
            _, was_created = Seat_Chart.objects.get_or_create(
                train=train,
                date=target_date,
                defaults={
                    "first_ac": 10,
                    "second_ac": 20,
                    "third_ac": 30,
                    "sleeper": 40
                }
            )
            if was_created:
                created += 1

    messages.success(request, f"✅ {created} seat charts created for {len(trains)} train(s).")


# ───── STATION ─────
@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "state", "zone", "address")
    search_fields = ("code", "name", "state", "zone")
    list_filter = ("zone", "state")
    ordering = ("code",)


# ───── SCHEDULE INLINE for Train Admin ─────
class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 0
    autocomplete_fields = ("station",)
    fields = ("station", "stop_order", "arrival", "departure", "day")
    ordering = ("stop_order",)
    show_change_link = True


# ───── TRAIN ─────
@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "source", "destination", "departure", "arrival", "zone", "train_type")
    search_fields = ("number", "name", "zone", "train_type")
    list_filter = ("zone", "train_type")
    autocomplete_fields = ("source", "destination")
    ordering = ("number",)
    fieldsets = (
        (None, {"fields": ("number", "name", "source", "destination")}),
        ("Timings & Type", {"fields": ("arrival", "departure", "return_train", "train_type", "zone")}),
        ("Stats", {"fields": ("duration_h", "duration_m", "distance")}),
    )
    inlines = [ScheduleInline]


# ───── SCHEDULE ─────
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("train", "station", "stop_order", "day", "arrival", "departure")
    search_fields = ("train__name", "train__number", "station__name", "station__code")
    list_filter = ("day",)
    autocomplete_fields = ("train", "station")
    ordering = ("train", "stop_order")
    list_editable = ("stop_order",)
    actions = [generate_charts_from_schedules]


# ───── SEAT CHART ─────
@admin.register(Seat_Chart)
class SeatChartAdmin(admin.ModelAdmin):
    list_display = ("train", "date", "first_ac", "second_ac", "third_ac", "sleeper")
    search_fields = ("train__name", "train__number")
    list_filter = ("date", "train")
    autocomplete_fields = ("train",)
    ordering = ("-date",)
    date_hierarchy = "date"


# ───── TICKET ─────
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("passenger", "train", "type", "fare", "date", "user", "confirmed")
    search_fields = ("passenger", "train__name", "train__number", "user__username")
    list_filter = ("type", "date", "confirmed")
    autocomplete_fields = (
        "user", "train", "chart",
        "source", "destination",
        "source_schedule", "destination_schedule"
    )
    readonly_fields = ("fare",)
    ordering = ("-date",)
    fieldsets = (
        (None, {"fields": ("passenger", "user", "train", "chart", "type", "fare", "date", "confirmed")}),
        ("Route", {"fields": ("source", "destination", "source_schedule", "destination_schedule")}),
    )