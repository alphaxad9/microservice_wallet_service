# src/application/booking/urls.py

from django.urls import path
from .command_views import (
    create_booking,
    confirm_booking,
    cancel_booking,
    expire_booking,
    check_in_booking,
    check_out_booking,
    update_booking_dates,
    change_booking_room,
    update_booking_price,
    delete_booking,
)
from .query_views import (
    get_booking,
    get_booking_with_guest,
    get_bookings_by_guest,
    get_bookings_by_guest_with_guest,
    get_bookings_by_room,
    get_active_bookings,
    get_bookings_by_status,
    count_bookings_by_status_view,
    booking_exists_view,
    is_room_available_view,
)

app_name = "booking"

urlpatterns = [
    # -------------------------
    # Command Endpoints (Write)
    # -------------------------
    path("", create_booking, name="create"),

    path("<uuid:booking_id>/confirm/", confirm_booking, name="confirm"),
    path("<uuid:booking_id>/cancel/", cancel_booking, name="cancel"),
    path("<uuid:booking_id>/expire/", expire_booking, name="expire"),
    path("<uuid:booking_id>/check-in/", check_in_booking, name="check_in"),
    path("<uuid:booking_id>/check-out/", check_out_booking, name="check_out"),

    path("<uuid:booking_id>/dates/", update_booking_dates, name="update_dates"),
    path("<uuid:booking_id>/room/", change_booking_room, name="change_room"),
    path("<uuid:booking_id>/price/", update_booking_price, name="update_price"),

    path("<uuid:booking_id>/", delete_booking, name="delete"),

    # -------------------------
    # Query Endpoints (Read)
    # -------------------------
    path("<uuid:booking_id>/detail/", get_booking, name="get_booking"),
    path("<uuid:booking_id>/detail-with-guest/", get_booking_with_guest, name="get_booking_with_guest"),

    path("guest/<uuid:guest_id>/", get_bookings_by_guest, name="get_bookings_by_guest"),
    path("guest/<uuid:guest_id>/with-guest/", get_bookings_by_guest_with_guest, name="get_bookings_by_guest_with_guest"),

    path("room/<uuid:room_id>/", get_bookings_by_room, name="get_bookings_by_room"),

    path("active/", get_active_bookings, name="get_active_bookings"),

    path("status/<str:status_name>/", get_bookings_by_status, name="get_bookings_by_status"),
    path("status/<str:status_name>/count/", count_bookings_by_status_view, name="count_bookings_by_status"),

    path("exists/<uuid:booking_id>/", booking_exists_view, name="booking_exists"),

    path("availability/", is_room_available_view, name="is_room_available"),
]