from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from helpers import (
    is_holiday_week, member_capacity, member_week_hours, risk_from_score,
    traffic_light_status, week_keys, weeks_between,
)


@dataclass
class FakeMember:
    id: str
    hours_per_week: int = 40


@dataclass
class FakeAssignment:
    member_id: str
    hours_per_week: int


@dataclass
class FakeAudit:
    start_week: str
    end_week: str
    budgeted_hours: int = 100
    completion_pct: int = 0
    phase: str = "Planning"
    assignments: list = field(default_factory=list)


def _monday(offset_weeks: int = 0) -> str:
    d = date.today() - timedelta(days=date.today().weekday())
    return (d + timedelta(weeks=offset_weeks)).isoformat()


def test_week_keys_count_and_history():
    assert len(week_keys()) == 52
    assert len(week_keys(history=4)) == 56
    keys = week_keys(history=2)
    assert keys[2] == _monday(0)


def test_weeks_between_inclusive_and_floor():
    assert weeks_between(_monday(0), _monday(0)) == 1
    assert weeks_between(_monday(0), _monday(3)) == 4
    # end before start floors at 1
    assert weeks_between(_monday(3), _monday(0)) == 1


def test_risk_from_score_bands():
    assert risk_from_score(1, 1) == "Low"
    assert risk_from_score(2, 3) == "Medium"
    assert risk_from_score(3, 4) == "High"
    assert risk_from_score(4, 4) == "Critical"


def test_member_capacity_part_time_and_holiday():
    full = FakeMember("a", 40)
    part = FakeMember("b", 20)
    assert member_capacity(full) == 40
    assert member_capacity(part) == 20
    holiday = next((w for w in week_keys() if is_holiday_week(w)), None)
    if holiday:
        assert member_capacity(full, holiday) == 32
        assert member_capacity(part, holiday) == 12


def test_member_week_hours_sums_overlapping_audits():
    weeks = week_keys()
    m = FakeMember("m1")
    a1 = FakeAudit(weeks[0], weeks[3], assignments=[FakeAssignment("m1", 10)])
    a2 = FakeAudit(weeks[2], weeks[5], assignments=[FakeAssignment("m1", 15)])
    out = member_week_hours([a1, a2], [m], weeks)
    assert out["m1"][weeks[0]] == 10
    assert out["m1"][weeks[2]] == 25
    assert out["m1"][weeks[4]] == 15
    assert out["m1"][weeks[6]] == 0


def test_traffic_light_over_budget_is_red():
    weeks = week_keys()
    a = FakeAudit(weeks[0], weeks[3], budgeted_hours=100,
                  assignments=[FakeAssignment("m1", 30)])  # 30*4=120 > 110
    assert traffic_light_status(a) == "Red"


def test_traffic_light_behind_schedule_is_red():
    weeks = week_keys()
    a = FakeAudit(weeks[0], weeks[0], budgeted_hours=1000,
                  completion_pct=10, phase="Fieldwork")
    assert traffic_light_status(a) == "Red"


def test_traffic_light_early_fieldwork_is_yellow():
    weeks = week_keys()
    a = FakeAudit(weeks[0], weeks[40], budgeted_hours=1000,
                  completion_pct=10, phase="Fieldwork")
    assert traffic_light_status(a) == "Yellow"


def test_traffic_light_healthy_is_green():
    weeks = week_keys()
    a = FakeAudit(weeks[0], weeks[40], budgeted_hours=1000,
                  completion_pct=60, phase="Fieldwork",
                  assignments=[FakeAssignment("m1", 10)])
    assert traffic_light_status(a) == "Green"
