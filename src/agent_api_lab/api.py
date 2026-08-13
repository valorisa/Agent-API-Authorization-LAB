"""Small local API authorization laboratory.

The module deliberately exposes two implementations:

- VulnerableReservationAPI reproduces a BOLA-style authorization flaw.
- FixedReservationAPI enforces object ownership server-side.

The implementation is intentionally dependency-free so the laboratory
can run in a minimal Python environment.
"""

from dataclasses import dataclass
from typing import Final


class AuthorizationError(Exception):
    """Raised when an authenticated user cannot access an object."""


class NotFoundError(Exception):
    """Raised when the requested object does not exist."""


@dataclass
class Reservation:
    """A reservation owned by one authenticated user."""

    reservation_id: str
    owner_id: str
    course_id: str
    status: str = "active"


class ReservationStore:
    """In-memory reservation store used by the laboratory."""

    def __init__(self) -> None:
        self._reservations: dict[str, Reservation] = {}

    def add(self, reservation: Reservation) -> None:
        self._reservations[reservation.reservation_id] = reservation

    def get(self, reservation_id: str) -> Reservation:
        try:
            return self._reservations[reservation_id]
        except KeyError as exc:
            raise NotFoundError(reservation_id) from exc


class VulnerableReservationAPI:
    """Intentionally vulnerable API.

    Authentication is assumed to have already succeeded. The vulnerable
    endpoint trusts the supplied object identifier and does not verify
    ownership before changing the reservation.
    """

    HTTP_OK: Final[int] = 200

    def __init__(self, store: ReservationStore) -> None:
        self.store = store

    def cancel_reservation(
        self,
        authenticated_user: str,
        reservation_id: str,
    ) -> int:
        """Cancel a reservation without checking its owner."""

        del authenticated_user
        reservation = self.store.get(reservation_id)
        reservation.status = "cancelled"
        return self.HTTP_OK


class FixedReservationAPI(VulnerableReservationAPI):
    """Corrected API with server-side object authorization."""

    HTTP_FORBIDDEN: Final[int] = 403

    def cancel_reservation(
        self,
        authenticated_user: str,
        reservation_id: str,
    ) -> int:
        """Cancel a reservation only when the user owns the object."""

        reservation = self.store.get(reservation_id)

        if reservation.owner_id != authenticated_user:
            raise AuthorizationError(
                "authenticated user does not own the reservation"
            )

        reservation.status = "cancelled"
        return self.HTTP_OK
