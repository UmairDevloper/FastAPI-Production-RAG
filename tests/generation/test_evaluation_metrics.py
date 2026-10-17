def test_abstention_metrics_count_only_expected_cases():
    results = [
        {"error": None, "expect_abstention": True, "abstention_pass": True},
        {"error": None, "expect_abstention": True, "abstention_pass": False},
        {"error": None, "expect_abstention": False, "abstention_pass": True},
        {"error": "RuntimeError: failed"},
    ]

    completed = [item for item in results if item.get("error") is None]
    abstention_cases = [
        item for item in completed if item.get("expect_abstention") is True
    ]
    abstention_passes = sum(
        item.get("abstention_pass") is True for item in abstention_cases
    )

    assert len(abstention_cases) == 2
    assert abstention_passes == 1
