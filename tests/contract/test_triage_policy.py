import json
from itertools import product
from pathlib import Path

import pytest

from supportops.domain.priority_matrix import Impact, Priority, Urgency
from supportops.errors import ConfigurationError
from supportops.triage_policy import default_policy_path, load_triage_policy


def write_policy(tmp_path: Path, mutation: object) -> Path:
    payload = json.loads(default_policy_path().read_text(encoding="utf-8"))
    if callable(mutation):
        mutation(payload)
    path = tmp_path / "test-policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_t3_cfg_01_valid_policy_loads_with_revision() -> None:
    policy = load_triage_policy()
    assert policy.policy_id == "supportops-triage"
    assert policy.schema_version == "1"
    assert len(policy.checksum) == 64
    assert policy.fallback_behavior == "fail_closed"


def test_t3_cfg_02_exact_cartesian_matrix() -> None:
    policy = load_triage_policy()
    assert {(rule.impact, rule.urgency) for rule in policy.matrix_rules} == set(
        product(Impact, Urgency)
    )
    assert len({rule.rule_id for rule in policy.matrix_rules}) == 16


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(lambda p: p["matrix_rules"].pop(), id="T3-CFG-03-missing"),
        pytest.param(
            lambda p: p["matrix_rules"].append(p["matrix_rules"][0]),
            id="T3-CFG-04-duplicate",
        ),
        pytest.param(
            lambda p: p["matrix_rules"][0].update(impact="extreme"),
            id="T3-CFG-05-enum",
        ),
        pytest.param(lambda p: p.update(schema_version="2"), id="T3-CFG-07-version"),
        pytest.param(
            lambda p: p["matrix_rules"][0].update(priority="P1"),
            id="T3-CFG-08-p1-boundary",
        ),
        pytest.param(
            lambda p: p.update(fallback_behavior="embedded_default"),
            id="T3-CFG-10-no-fallback",
        ),
    ],
)
def test_invalid_policy_fails_closed(tmp_path: Path, mutation: object) -> None:
    path = write_policy(tmp_path, mutation)
    with pytest.raises(ConfigurationError):
        load_triage_policy(path)


def test_t3_cfg_06_malformed_or_missing_is_safe(tmp_path: Path) -> None:
    malformed = tmp_path / "canary-secret-policy.json"
    malformed.write_text("{TOKEN=secret", encoding="utf-8")
    with pytest.raises(ConfigurationError) as captured:
        load_triage_policy(malformed)
    assert "TOKEN=secret" not in captured.value.public_message
    assert str(tmp_path) not in captured.value.public_message
    with pytest.raises(ConfigurationError):
        load_triage_policy(tmp_path / "missing.json")


def test_t3_cfg_09_error_does_not_expose_contents_or_absolute_path(
    tmp_path: Path,
) -> None:
    path = tmp_path / "safe-name.json"
    path.write_text('{"password":"do-not-leak"}', encoding="utf-8")
    with pytest.raises(ConfigurationError) as captured:
        load_triage_policy(path)
    assert "do-not-leak" not in captured.value.public_message
    assert str(tmp_path) not in captured.value.public_message
    assert "safe-name.json" in captured.value.public_message


def test_t3_pri_01_to_04_matrix_and_invariants_are_exact() -> None:
    policy = load_triage_policy()
    expected = {
        ("low", "low"): "P4",
        ("low", "moderate"): "P3",
        ("low", "high"): "P2",
        ("low", "critical"): "P2",
        ("moderate", "low"): "P3",
        ("moderate", "moderate"): "P3",
        ("moderate", "high"): "P2",
        ("moderate", "critical"): "P2",
        ("high", "low"): "P2",
        ("high", "moderate"): "P2",
        ("high", "high"): "P2",
        ("high", "critical"): "P2",
        ("critical", "low"): "P2",
        ("critical", "moderate"): "P2",
        ("critical", "high"): "P2",
        ("critical", "critical"): "P1",
    }
    found = {
        (rule.impact.value, rule.urgency.value): rule.priority.value
        for rule in policy.matrix_rules
    }
    assert found == expected
    assert [rule for rule in policy.matrix_rules if rule.priority is Priority.P1] == [
        policy.matrix_rule(Impact.CRITICAL, Urgency.CRITICAL)
    ]
    assert load_triage_policy().model_dump() == load_triage_policy().model_dump()


def test_matrix_boundary_configuration_is_fail_closed(tmp_path: Path) -> None:
    def remove_hc_boundary(payload: dict[str, object]) -> None:
        rules = payload["matrix_rules"]
        assert isinstance(rules, list)
        hc = next(rule for rule in rules if rule["rule_id"] == "MX-HC")
        hc.pop("stop_rule_ids")

    with pytest.raises(ConfigurationError):
        load_triage_policy(write_policy(tmp_path, remove_hc_boundary))
