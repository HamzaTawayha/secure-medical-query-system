from benchmark_generator import generate_benchmark


def test_benchmark_generation_is_deterministic_without_writing():
    first = generate_benchmark(seed=7, n_patients=40, n_users=12, n_events=120, write_csv=False)
    second = generate_benchmark(seed=7, n_patients=40, n_users=12, n_events=120, write_csv=False)

    assert first["events"].equals(second["events"])
    assert set(["event_id", "label", "scenario", "risk_tier"]).issubset(first["events"].columns)
    assert {"patients", "encounters", "users", "relationships", "notes", "events"} == set(first.keys())
