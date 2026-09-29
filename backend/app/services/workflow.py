"""The request status machine, as data.

    submitted -> in_progress -> delivered -> accepted
                                          \\-> rejected -> in_progress (rework)

Each allowed transition maps to the roles that own that step. Anything not in the
table is invalid. Keeping this as a single table makes the rules easy to read, test
exhaustively and change.
"""

from app.models import RequestStatus as S
from app.models import Role

STAFF = frozenset({Role.OPERATOR, Role.ADMIN})
CLIENT = frozenset({Role.CLIENT})

TRANSITIONS: dict[tuple[S, S], frozenset[Role]] = {
    (S.SUBMITTED, S.IN_PROGRESS): STAFF,
    (S.IN_PROGRESS, S.DELIVERED): STAFF,
    (S.DELIVERED, S.ACCEPTED): CLIENT,
    (S.DELIVERED, S.REJECTED): CLIENT,
    (S.REJECTED, S.IN_PROGRESS): STAFF,
}


def allowed_roles(current: S, target: S) -> frozenset[Role] | None:
    """Roles that may perform current -> target, or None if the transition doesn't exist."""
    return TRANSITIONS.get((current, target))


def next_statuses(current: S, role: Role) -> list[S]:
    """Transitions this role can make from `current` (used to drive the UI's buttons)."""
    return [to for (frm, to), roles in TRANSITIONS.items() if frm == current and role in roles]
