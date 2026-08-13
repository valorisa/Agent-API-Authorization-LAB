"""Authorization regression tests for the laboratory."""

import pytest

from agent_api_lab.api import (
    AuthorizationError,
    FixedReservationAPI,
    Reservation,
    ReservationStore,
    VulnerableReservationAPI,
)


@pytest.fixture
def store() -> ReservationStore:
    store = ReservationStore()
    store.add(
        Reservation(
            reservation_id="reservation-alice",
            owner_id="alice",
            course_id="course-101",
        )
    )
    return store


def test_vulnerable_api_allows_cross_user_cancellation(
    store: ReservationStore,
) -> None:
    api = VulnerableReservationAPI(store)

    status = api.cancel_reservation(
        authenticated_user="bob",
        reservation_id="reservation-alice",
    )

    assert status == 200
    assert store.get("reservation-alice").status == "cancelled"


def test_fixed_api_rejects_cross_user_cancellation(
    store: ReservationStore,
) -> None:
    api = FixedReservationAPI(store)

    with pytest.raises(AuthorizationError):
        api.cancel_reservation(
            authenticated_user="bob",
            reservation_id="reservation-alice",
        )

    assert store.get("reservation-alice").status == "active"


def test_fixed_api_allows_owner_cancellation(
    store: ReservationStore,
) -> None:
    api = FixedReservationAPI(store)

    status = api.cancel_reservation(
        authenticated_user="alice",
        reservation_id="reservation-alice",
    )

    assert status == 200
    assert store.get("reservation-alice").status == "cancelled"
