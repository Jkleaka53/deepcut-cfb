import pytest
import responses

from cfbm.cfbd_client import CfbdClient, CfbdError

BASE = "https://api.collegefootballdata.com"


@responses.activate
def test_get_sends_bearer_and_caches(tmp_path):
    responses.get(f"{BASE}/games", json=[{"id": 1}])
    c = CfbdClient("KEY", tmp_path)
    assert c.get("/games", {"year": 2025, "week": 1}) == [{"id": 1}]
    assert c.get("/games", {"week": 1, "year": 2025}) == [{"id": 1}]  # param order irrelevant
    assert len(responses.calls) == 1 and c.calls_made == 1
    assert responses.calls[0].request.headers["Authorization"] == "Bearer KEY"


@responses.activate
def test_different_params_are_different_cache_entries(tmp_path):
    responses.get(f"{BASE}/games", json=[{"id": 1}])
    c = CfbdClient("KEY", tmp_path)
    c.get("/games", {"year": 2025, "week": 1})
    c.get("/games", {"year": 2025, "week": 2})
    assert c.calls_made == 2


@responses.activate
def test_uncacheable_always_refetches(tmp_path):
    responses.get(f"{BASE}/games", json=[{"id": 1}])
    c = CfbdClient("KEY", tmp_path)
    c.get("/games", {"year": 2026}, cacheable=False)
    c.get("/games", {"year": 2026}, cacheable=False)
    assert len(responses.calls) == 2


@responses.activate
def test_incomplete_then_complete_week_refetches(tmp_path):
    # Wednesday: week in progress (uncacheable). Sunday: week complete (cacheable) must NOT reuse Wednesday's data.
    responses.get(f"{BASE}/plays", json=[{"id": "partial"}])
    responses.get(f"{BASE}/plays", json=[{"id": "partial"}, {"id": "saturday"}])
    c = CfbdClient("KEY", tmp_path)
    c.get("/plays", {"year": 2026, "week": 12}, cacheable=False)
    assert c.get("/plays", {"year": 2026, "week": 12}) == [{"id": "partial"}, {"id": "saturday"}]
    assert len(responses.calls) == 2


@responses.activate
def test_error_raises_with_status(tmp_path):
    responses.get(f"{BASE}/plays", status=429)
    with pytest.raises(CfbdError, match="429"):
        CfbdClient("KEY", tmp_path).get("/plays", {"year": 2025})
