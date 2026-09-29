"""Domain enumerations. Stored as VARCHAR + CHECK (not native PG enums) so that
adding a value later is a one-line migration instead of an ALTER TYPE dance."""

from enum import Enum


class Role(str, Enum):
    CLIENT = "client"
    OPERATOR = "operator"
    ADMIN = "admin"


class Quality(str, Enum):
    GOOD = "good"
    USABLE = "usable"
    BAD = "bad"


class RequestStatus(str, Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


ASSIGNABLE_QUALITIES = frozenset({Quality.GOOD, Quality.USABLE})
