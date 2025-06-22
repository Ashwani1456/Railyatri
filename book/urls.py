from django.urls import path
from . import views
from .views import CancelTicket

app_name = "book"

urlpatterns = [
    # 🏠 Home & Search
    path("", views.homeView, name="home"),
    path("search/", views.searchView, name="search"),
    path("map-search/", views.searchView, name="mapSearch"),  # You can separate this if needed

    # 🔍 Complex Search
    path(
        "complexSearch/<str:source>-<str:dest>/<str:date>/",
        views.complexSearchView,
        name="complexSearch"
    ),

    # 🎟️ Booking (Single & Multi-leg)
    path("book/<str:train_id>/<str:date>/", views.bookView, name="book"),
    path(
        "complexBook/<int:chart1>/<int:chart2>/<int:src>/<int:via1>/<int:via2>/<int:dest>/<str:class_type>/<str:date>/",
        views.complexBookView,
        name="complexBook"
    ),

    # 🧾 Ticket Actions
    path("confirm/<int:ticket_id>/", views.confirmTicketView, name="confirm"),
    path("cancel/<int:pk>/", CancelTicket.as_view(), name="cancel"),

    # 👤 User Profile
    path("profile/", views.profileView, name="profile"),
    path("book-ticket/", views.inlineTicketBookView, name="book_ticket"),

    # ⚙️ API Endpoints (optional grouping)
    # path("api/station-autocomplete/", views.station_autocomplete_view, name="station-autocomplete"),
]