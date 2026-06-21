import numpy as np
import pandas as pd

from app import app, cache
from tseapy.agent import engine


def _load_multifeature_dataset():
    """Populate the agent cache and run the agent synchronously for tests."""
    rng = np.random.default_rng(0)
    n = 200
    t = np.arange(n)
    frame = pd.DataFrame(
        {
            "a": 0.05 * t + rng.normal(0, 1, n),
            "b": 0.1 * t + rng.normal(0, 1, n),
            "c": rng.normal(0, 1, n),
        },
        index=pd.date_range("2024-01-01", periods=n, freq="h"),
    )
    cache.set("agent_data", frame)
    cache.set("data", frame[["a"]])
    engine.reset()
    engine.start(frame, background=False)


def test_agent_dashboard_redirects_without_data():
    with app.test_client() as client:
        cache.delete("agent_data")
        cache.delete("data")
        engine.reset()
        resp = client.get("/agent")
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/upload")


def test_agent_dashboard_renders_with_data():
    with app.test_client() as client:
        _load_multifeature_dataset()
        resp = client.get("/agent")
        assert resp.status_code == 200
        assert b"Insights Agent" in resp.data


def test_agent_status_reports_done():
    with app.test_client() as client:
        _load_multifeature_dataset()
        payload = client.get("/agent/status").get_json()
        assert payload["status"] == "done"
        assert payload["completed"] == payload["total"]


def test_agent_findings_listed_and_ranked():
    with app.test_client() as client:
        _load_multifeature_dataset()
        findings = client.get("/agent/findings").get_json()["findings"]
        assert findings
        scores = [f["score"] for f in findings]
        assert scores == sorted(scores, reverse=True)
        assert "figure_spec" not in findings[0]


def test_agent_finding_figure_built_on_demand():
    with app.test_client() as client:
        _load_multifeature_dataset()
        findings = client.get("/agent/findings").get_json()["findings"]
        finding_id = findings[0]["id"]
        resp = client.get(f"/agent/findings/{finding_id}/figure")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "data" in body and "layout" in body


def test_agent_unknown_finding_returns_404():
    with app.test_client() as client:
        _load_multifeature_dataset()
        resp = client.get("/agent/findings/does-not-exist/figure")
        assert resp.status_code == 404


def test_configure_populates_agent_data_and_starts_agent():
    import io

    with app.test_client() as client:
        cache.delete("agent_data")
        cache.delete("data")
        cache.delete("raw_data")
        engine.reset()
        rng = np.random.default_rng(1)
        n = 120
        df = pd.DataFrame(
            {
                "time": pd.date_range("2024-01-01", periods=n, freq="h").strftime("%Y-%m-%d %H:%M:%S"),
                "x": np.arange(n, dtype=float) + rng.normal(0, 1, n),
                "y": rng.normal(0, 1, n),
            }
        )
        csv = df.to_csv(index=False).encode()
        client.post(
            "/upload",
            data={"file": (io.BytesIO(csv), "d.csv")},
            content_type="multipart/form-data",
        )
        resp = client.post(
            "/upload/configure",
            data={"time_column": "time", "value_column": "x", "confirm_selection": "on"},
        )
        assert resp.status_code == 302
        agent_frame = cache.get("agent_data")
        assert agent_frame is not None
        # Both numeric columns are retained for cross-feature analysis.
        assert set(agent_frame.columns) == {"x", "y"}
