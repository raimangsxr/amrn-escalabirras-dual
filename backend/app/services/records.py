"""Record-detection logic for crate adjustments."""

from __future__ import annotations


def compute_is_new_record(current_crates: int, previous_max: int | None) -> bool:
    """Return ``True`` if the current run just set a new all-time record.

    A run is considered a record iff its crate count strictly exceeds
    every other participant's crates seen in the same transaction. If
    there were no other participants (``previous_max is None``), the
    very first crate makes it a record (current_crates >= 1).
    """
    if previous_max is None:
        return current_crates >= 1
    return current_crates > previous_max