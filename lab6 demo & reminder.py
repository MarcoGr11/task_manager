"""Lab 6 hook demo: how often to remind the owner about an open task."""

REMINDER_HOURS = {  # (priority, overdue, weekend) -> hours
    ("HIGH", True, True): 4, ("HIGH", True, False): 1, ("HIGH", False, True): 12, ("HIGH", False, False): 4,
    ("MEDIUM", True, True): 12, ("MEDIUM", True, False): 4, ("MEDIUM", False, True): 48, ("MEDIUM", False, False): 24,
}
OTHER_PRIORITY_HOURS = {(True, True): 24, (True, False): 24, (False, True): 96, (False, False): 72}


def reminder_hours(priority: str, overdue: bool, weekend: bool, has_owner: bool) -> int:
    if not has_owner:
        return 1
    return REMINDER_HOURS.get((priority, overdue, weekend), OTHER_PRIORITY_HOURS[(overdue, weekend)])
