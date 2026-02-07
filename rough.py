from app.api.generation import _try_parse_json_from_text


def test_try_parse_json_from_text_dict_passthrough():
    data = {"a": 1}
    assert _try_parse_json_from_text(data) == data


def test_try_parse_json_from_text_none_input():
    assert _try_parse_json_from_text(None) is None


def test_try_parse_json_from_text_invalid_string():
    assert _try_parse_json_from_text("not json at all") is None


def test_try_parse_json_from_text_plain_json():
    text = '{"a": 1, "b": 2}'
    assert _try_parse_json_from_text(text) == {"a": 1, "b": 2}


def test_try_parse_json_from_text_embedded_json():
    text = "some text before {\"x\": 10} some text after"
    assert _try_parse_json_from_text(text) == {"x": 10}


def test_try_parse_json_from_text_malformed_json():
    text = "{bad json}"
    assert _try_parse_json_from_text(text) is None
