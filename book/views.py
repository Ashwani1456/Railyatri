import logging
from datetime import timedelta
from dateutil import parser

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import Station, Train, Schedule, Seat_Chart, Ticket

logger = logging.getLogger(__name__)

# ───── Constants ─────
RATE_MAP = {"1A": 20, "2A": 15, "3A": 10, "SL": 5}
DEFAULT_SEATS = {"first_ac": 10, "second_ac": 20, "third_ac": 30, "sleeper": 40}


# ───── Utility Functions ─────

def _parse_date(date_str):
    try:
        return parser.parse(date_str).date()
    except Exception:
        return None

def _get_schedule(train, station):
    return Schedule.objects.filter(train=train, station=station).first()

def _calculate_fare(length):
    return {cls: length * rate for cls, rate in RATE_MAP.items()}

def _ensure_seat_chart(train, travel_date):
    return Seat_Chart.objects.get_or_create(
        train=train,
        date=travel_date,
        defaults=DEFAULT_SEATS
    )


# ───── Views ─────

@login_required(login_url="/login")
def homeView(request):
    stations = Station.objects.all()
    return render(request, "book/home.html", {"stations": stations})


@login_required(login_url="/login")
def searchView(request):
    stations = Station.objects.all()

    if request.method != "POST":
        return render(request, "book/trainSearch.html", {"stations": stations})

    source_code = request.POST.get("source")
    dest_code = request.POST.get("dest")
    date_input = request.POST.get("journey_date")
    journey_date = _parse_date(date_input)

    # Get Station instances, return None if not found
    source = Station.objects.filter(pk=source_code).first()
    dest = Station.objects.filter(pk=dest_code).first()

    # Handle invalid input quietly and preserve form state
    if not source or not dest or not journey_date:
        return render(request, "book/trainSearch.html", {
            "stations": stations,
            "prefill_source": source_code,
            "prefill_dest": dest_code,
            "prefill_date": date_input,
            "invalid_station": not source or not dest,
            "invalid_date": not journey_date
        })

    # Compile matching trains
    results = []
    for train in Train.objects.all():
        if not (source.stop_schedules.filter(train=train).exists() and
                dest.stop_schedules.filter(train=train).exists()):
            continue

        src_sched = _get_schedule(train, source)
        dst_sched = _get_schedule(train, dest)

        if not src_sched or not dst_sched or src_sched.stop_order >= dst_sched.stop_order:
            continue

        chart, _ = _ensure_seat_chart(train, journey_date)
        segment_length = dst_sched.stop_order - src_sched.stop_order
        fare = _calculate_fare(segment_length)
        seats = {cls: chart.get_available_seats(cls) for cls in RATE_MAP}

        results.append((train, src_sched, dst_sched, seats, fare))

    return render(request, "book/trainSearch.html", {
        "stations": stations,
        "results": results,
        "source": source,
        "dest": dest,
        "date": journey_date.strftime("%Y-%m-%d"),
        "class_types": list(RATE_MAP),
        "prefill_source": source_code,
        "prefill_dest": dest_code,
        "prefill_date": date_input
    })

@login_required(login_url="/login")
def complexSearchView(request, source, dest, date):
    source_station = Station.objects.filter(code=source).first()
    dest_station = Station.objects.filter(code=dest).first()
    journey_date = _parse_date(date)

    if not source_station or not dest_station:
        return render(request, "book/connectingTrainSearch.html", {
            "invalid_station": True,
            "source_code": source,
            "dest_code": dest
        })

    if not journey_date:
        return render(request, "book/connectingTrainSearch.html", {"error": "Invalid travel date."})

    source_trains = {s.train for s in source_station.stop_schedules.select_related("train")}
    dest_trains = {s.train for s in dest_station.stop_schedules.select_related("train")}

    inter_stations = {
        s.station for t in source_trains for s in t.schedules.select_related("station")
    } & {
        s.station for t in dest_trains for s in t.schedules.select_related("station")
    }

    results = []
    for inter in inter_stations:
        for t1 in source_trains:
            src = _get_schedule(t1, source_station)
            via1 = _get_schedule(t1, inter)
            if not src or not via1 or src.stop_order >= via1.stop_order:
                continue

            for t2 in dest_trains:
                via2 = _get_schedule(t2, inter)
                dst = _get_schedule(t2, dest_station)
                if not via2 or not dst or via2.stop_order >= dst.stop_order:
                    continue
                if not via1.arrival or not via2.departure or via1.arrival >= via2.departure:
                    continue

                chart1, _ = _ensure_seat_chart(t1, journey_date)
                chart2, _ = _ensure_seat_chart(t2, journey_date)

                segment = (via1.stop_order - src.stop_order) + (dst.stop_order - via2.stop_order)
                fare = _calculate_fare(segment)
                results.append((t1, t2, src, via1, via2, dst, chart1, chart2, fare))

    return render(request, "book/connectingTrainSearch.html", {
        "source": source_station,
        "dest": dest_station,
        "results": results,
        "date": date,
        "class_types": list(RATE_MAP),
        "no_result": not results
    })


@login_required(login_url="/login")
def bookView(request, train_id, date):
    train = get_object_or_404(Train, pk=train_id)
    journey_date = _parse_date(date)
    if not journey_date:
        return render(request, "book/booking.html", {"error": "Invalid travel date."})

    chart = get_object_or_404(Seat_Chart, train=train, date=journey_date)
    return render(request, "book/booking.html", {
        "train": train,
        "chart": chart,
        "date": date
    })
@login_required(login_url="/login")
def complexBookView(request, chart1, chart2, src, via1, via2, dest, class_type, date):
    journey_date = _parse_date(date)
    if not journey_date:
        return render(request, "book/booking.html", {"error": "Invalid travel date."})

    ctx = {
        "chart1": get_object_or_404(Seat_Chart, pk=chart1),
        "chart2": get_object_or_404(Seat_Chart, pk=chart2),
        "sourceSchedule": get_object_or_404(Schedule, pk=src),
        "commonSchedule1": get_object_or_404(Schedule, pk=via1),
        "commonSchedule2": get_object_or_404(Schedule, pk=via2),
        "destSchedule": get_object_or_404(Schedule, pk=dest),
        "type": class_type,
        "date": date,
    }

    ctx["train1"] = ctx["chart1"].train
    ctx["train2"] = ctx["chart2"].train
    ctx["source"] = ctx["sourceSchedule"].station
    ctx["dest"] = ctx["destSchedule"].station

    return render(request, "book/booking.html", ctx)


@login_required(login_url="/login")
def inlineTicketBookView(request):
    if request.method == "POST":
        train_id = request.POST.get("train")
        class_type = request.POST.get("class_type")
        date_str = request.POST.get("date")
        passenger = request.POST.get("passenger")

        train = get_object_or_404(Train, pk=train_id)
        journey_date = _parse_date(date_str)

        if not journey_date or class_type not in RATE_MAP:
            return redirect("book:home")

        chart = get_object_or_404(Seat_Chart, train=train, date=journey_date)
        source = train.source
        destination = train.destination
        src_schedule = _get_schedule(train, source)
        dest_schedule = _get_schedule(train, destination)

        if not src_schedule or not dest_schedule or src_schedule.stop_order >= dest_schedule.stop_order:
            return redirect("book:home")

        ticket = Ticket.objects.create(
            passenger=passenger,
            user=request.user,
            train=train,
            chart=chart,
            source=source,
            destination=destination,
            source_schedule=src_schedule,
            destination_schedule=dest_schedule,
            type=class_type,
            date=journey_date
        )
        ticket.calculate_fare(save=True)
        return redirect("book:profile")

    return redirect("book:home")


@login_required(login_url="/login")
def confirmTicketView(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    ticket.confirmed = True
    ticket.save()
    return redirect("book:profile")


@login_required(login_url="/login")
def profileView(request):
    tickets = Ticket.objects.filter(user=request.user).order_by("-date")
    return render(request, "book/profile.html", {"tickets": tickets})


class CancelTicket(LoginRequiredMixin, DeleteView):
    model = Ticket
    template_name = "book/ticket_confirm_delete.html"
    success_url = reverse_lazy("book:profile")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ticket"] = self.object
        return context