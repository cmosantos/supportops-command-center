from collections.abc import Callable
from itertools import product

import pytest
from pydantic import ValidationError

from supportops.domain.priority_matrix import (
    Impact,
    PriorityMatrixConfiguration,
    PriorityMatrixRule,
    Urgency,
)


def complete_rules() -> list[dict[str, str]]:
    return [
        {"impact": impact.value, "urgency": urgency.value, "priority": "P4"}
        for impact, urgency in product(Impact, Urgency)
    ]


def test_complete_matrix_contract_is_accepted() -> None:
    matrix = PriorityMatrixConfiguration.model_validate(
        {"schema_version": "1", "matrix_version": "test", "rules": complete_rules()}
    )

    assert len(matrix.rules) == 16
    assert not hasattr(matrix, "classify")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda rules: rules[:-1],
        lambda rules: [*rules, rules[0]],
    ],
)
def test_incomplete_or_conflicting_matrix_is_rejected(
    mutation: Callable[[list[dict[str, str]]], list[dict[str, str]]],
) -> None:
    with pytest.raises(ValidationError):
        PriorityMatrixConfiguration.model_validate(
            {
                "schema_version": "1",
                "matrix_version": "invalid",
                "rules": mutation(complete_rules()),
            }
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [("impact", "extreme"), ("urgency", "immediate"), ("priority", "P0")],
)
def test_invalid_enums_are_rejected(field: str, value: str) -> None:
    data = {"impact": "low", "urgency": "low", "priority": "P4"}
    data[field] = value

    with pytest.raises(ValidationError):
        PriorityMatrixRule.model_validate(data)


def test_extra_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        PriorityMatrixRule.model_validate(
            {"impact": "low", "urgency": "low", "priority": "P4", "extra": True}
        )
