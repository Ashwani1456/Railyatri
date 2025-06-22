from django.core.management.base import BaseCommand
from datetime import date, timedelta
from book.models import Train, Seat_Chart

DEFAULT_SEATS = {
    'first_ac': 10,
    'second_ac': 20,
    'third_ac': 30,
    'sleeper': 40,
}

class Command(BaseCommand):
    help = "Generate seat charts for all trains with schedules for the next N days (default: 7)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days ahead to create seat charts for (default: 7)',
        )

    def handle(self, *args, **options):
        days = options['days']
        today = date.today()
        created_count = 0
        skipped_count = 0

        trains = Train.objects.filter(schedules__isnull=False).distinct()

        self.stdout.write(f"📅 Generating seat charts for {trains.count()} train(s) for {days} day(s)...")

        for train in trains:
            for i in range(days):
                travel_date = today + timedelta(days=i)
                _, created = Seat_Chart.objects.get_or_create(
                    train=train,
                    date=travel_date,
                    defaults=DEFAULT_SEATS
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Created: {created_count} | Skipped (already exists): {skipped_count}"))