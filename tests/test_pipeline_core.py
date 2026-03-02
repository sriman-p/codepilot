from pathlib import Path

from reqlens.pipeline.code_analyzer import analyze_code
from reqlens.pipeline.mapper import map_requirements_to_code
from reqlens.pipeline.requirements_parser import parse_requirements


def test_pipeline_stages_parse_map_analyze() -> None:
    requirements = parse_requirements(Path("tests/fixtures/requirements.md"))
    code_elements = analyze_code(Path("tests/fixtures/sample_app"))
    mappings = map_requirements_to_code(requirements, code_elements, confidence_threshold=0.0)

    assert len(requirements) == 2
    assert len(code_elements) >= 2
    assert len(mappings) == len(requirements)
    assert all(m.requirement_id for m in mappings)
