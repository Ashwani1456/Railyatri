from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

# ───── STATION ─────
class Station(models.Model):
    code = models.CharField("Code", max_length=10, primary_key=True)
    name = models.CharField("Name", max_length=30)
    state = models.CharField("State", max_length=20, blank=True, null=True)
    zone = models.CharField("Zone", max_length=10, blank=True, null=True)
    address = models.CharField("Address", max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Station"
        verbose_name_plural = "Stations"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ───── TRAIN ─────
class Train(models.Model):
    number = models.CharField("Train Number", max_length=15, primary_key=True)
    name = models.CharField("Name", max_length=30)
    source = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, related_name="departing_trains")
    destination = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, related_name="arriving_trains")
    arrival = models.TimeField("Arrival Time", blank=True, null=True)
    departure = models.TimeField("Departure Time", blank=True, null=True)
    return_train = models.CharField("Return Train", max_length=15, blank=True, null=True)
    duration_h = models.PositiveSmallIntegerField("Duration Hours", blank=True, null=True)
    duration_m = models.PositiveSmallIntegerField("Duration Minutes", blank=True, null=True)
    train_type = models.CharField("Type", max_length=5, blank=True, null=True)
    distance = models.PositiveIntegerField("Distance (km)", blank=True, null=True)
    zone = models.CharField("Zone", max_length=10, blank=True, null=True)

    class Meta:
        verbose_name = "Train"
        verbose_name_plural = "Trains"
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.name}"


# ───── SCHEDULE ─────
class Schedule(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="schedules")
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="stop_schedules")
    stop_order = models.PositiveSmallIntegerField("Stop Order", default=0)
    day = models.PositiveSmallIntegerField("Day of Journey", blank=True, null=True)
    arrival = models.TimeField("Arrival Time", blank=True, null=True)
    departure = models.TimeField("Departure Time", blank=True, null=True)

    class Meta:
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"
        unique_together = ('train', 'station')
        ordering = ["train", "stop_order"]

    def __str__(self):
        return f"{self.train} @ {self.station}"

    def clean(self):
        if Schedule.objects.filter(train=self.train, station=self.station).exclude(pk=self.pk).exists():
            raise ValidationError("Duplicate schedule for this train and station.")


# ───── SEAT CHART ─────
class Seat_Chart(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="seat_charts")
    date = models.DateField("Travel Date")
    first_ac = models.PositiveIntegerField("1st AC")
    second_ac = models.PositiveIntegerField("2nd AC")
    third_ac = models.PositiveIntegerField("3rd AC")
    sleeper = models.PositiveIntegerField("Sleeper")

    class Meta:
        verbose_name = "Seat Chart"
        verbose_name_plural = "Seat Charts"
        unique_together = ('train', 'date')
        ordering = ["-date"]

    def __str__(self):
        return f"{self.train.number} on {self.date}"

    def get_available_seats(self, coach_type):
        inventory = {
            "1A": self.first_ac,
            "2A": self.second_ac,
            "3A": self.third_ac,
            "SL": self.sleeper
        }
        booked = self.chart_tickets.filter(type=coach_type).count()
        return inventory.get(coach_type, 0) - booked


# ───── TICKET ─────
class Ticket(models.Model):
    COACH_CHOICES = [
        ("1A", "First AC"),
        ("2A", "Second AC"),
        ("3A", "Third AC"),
        ("SL", "Sleeper"),
    ]

    passenger = models.CharField("Passenger Name", max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="tickets")
    chart = models.ForeignKey(Seat_Chart, on_delete=models.CASCADE, related_name="chart_tickets")
    source = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="tickets_from")
    destination = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="tickets_to", null=True)
    source_schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="departing_tickets")
    destination_schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="arriving_tickets", null=True)
    type = models.CharField("Coach Type", max_length=2, choices=COACH_CHOICES)
    date = models.DateField("Travel Date")
    fare = models.PositiveIntegerField("Fare", default=0)
    confirmed = models.BooleanField("Confirmed", default=False)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.passenger} - {self.train.number} on {self.date}"

    def calculate_fare(self, save=False):
        if self.source_schedule and self.destination_schedule and self.type:
            rate = {"1A": 20, "2A": 15, "3A": 10, "SL": 5}.get(self.type, 1)
            segment = abs(self.destination_schedule.stop_order - self.source_schedule.stop_order)
            self.fare = segment * rate
            if save:
                self.save()