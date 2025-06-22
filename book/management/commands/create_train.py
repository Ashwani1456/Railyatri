from django.core.management.base import BaseCommand
from book.models import Train, Station, Schedule
from datetime import time

class Command(BaseCommand):
    help = "Create a new train between two stations with dummy schedule"

    def add_arguments(self, parser):
        parser.add_argument("train_name", type=str)
        parser.add_argument("source_code", type=str)
        parser.add_argument("dest_code", type=str)

    def handle(self, *args, **options):
        train_name = options["train_name"]
        src_code = options["source_code"].upper()
        dst_code = options["dest_code"].upper()

        try:
            source = Station.objects.get(code=src_code)
            dest = Station.objects.get(code=dst_code)
        except Station.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Station code invalid."))
            return

        train_number = f"R{Train.objects.count()+1001}"
        train = Train.objects.create(
            number=train_number,
            name=train_name,
            source=source,
            destination=dest,
            departure=time(10, 0),
            arrival=time(18, 0),
            duration_h=8,
            duration_m=0,
            zone="Z",
            train_type="EXP"
        )

        Schedule.objects.create(train=train, station=source, stop_order=1, departure=time(10,0))
        Schedule.objects.create(train=train, station=dest, stop_order=2, arrival=time(18,0))

        self.stdout.write(self.style.SUCCESS(f"✅ Train {train_name} [{train_number}] added from {src_code} to {dst_code}"))