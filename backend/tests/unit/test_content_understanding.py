from app.services.content_understanding import CONFIDENCE_THRESHOLD, _map_result


class _Field:
    def __init__(self, value, confidence, source="page:1"):
        self.value_string = value
        self.confidence = confidence
        self.source = source


class _Result:
    def __init__(self, fields):
        self.fields = fields


def test_maps_fields_to_source_facts_with_confidence() -> None:
    result = _Result({"total_return": _Field("+3.2%", 0.95)})
    extraction = _map_result(result)
    assert len(extraction.facts) == 1
    fact = extraction.facts[0]
    assert fact.source_id == "cu:total_return"
    assert fact.value == "+3.2%"
    assert fact.confidence == 0.95
    assert extraction.needs_review == []


def test_low_confidence_field_flagged_for_review() -> None:
    low = CONFIDENCE_THRESHOLD - 0.1
    result = _Result({"chart_value": _Field("36.6%", low)})
    extraction = _map_result(result)
    assert "cu:chart_value" in extraction.needs_review
