"""
test/test_validate.py — repair_and_validate (trailing comma, markdown wrap, missing fields)
"""
import json, pytest


class TestRepairAndValidate:
    def test_trailing_comma_removed(self):
        from validate_outline import repair_and_validate
        bad = '{"slides": [{"type": "keep", "ref": "cover",},]}'
        repaired, warnings = repair_and_validate(bad)
        assert repaired is not None
        assert any('尾随逗号' in w or 'trailing' in w.lower() for w in warnings)
        data = json.loads(repaired)
        assert len(data['slides']) == 1

    def test_markdown_code_block_removed(self):
        from validate_outline import repair_and_validate
        bad = '```json\n{"slides":[]}\n```'
        repaired, warnings = repair_and_validate(bad)
        assert repaired is not None
        assert any('```' in w for w in warnings)
        data = json.loads(repaired)
        assert 'slides' in data

    def test_missing_meta_filled(self):
        from validate_outline import repair_and_validate
        bad = '{"slides": []}'
        repaired, warnings = repair_and_validate(bad)
        assert repaired is not None
        data = json.loads(repaired)
        assert 'meta' in data
        assert 'template_path' in data['meta']

    def test_body_string_to_list(self):
        from validate_outline import repair_and_validate
        bad = '{"slides": [{"type": "result", "title": "test", "body": "single string"}]}'
        repaired, warnings = repair_and_validate(bad)
        data = json.loads(repaired)
        body = data['slides'][0].get('body')
        assert isinstance(body, list)
        assert body == ['single string']

    def test_valid_example_passes(self):
        import os
        from validate_outline import validate
        ok = validate(os.path.join(
            os.path.dirname(__file__), '..', 'templates', 'example-slide-content.json'))
        assert ok
