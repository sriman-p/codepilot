"""Core domain schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    id: str
    text: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    priority: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class CodeElement(BaseModel):
    id: str
    file_path: str
    symbol_type: str
    qualified_name: str
    signature: str
    complexity: int = 1


class RequirementCodeMapping(BaseModel):
    requirement_id: str
    code_element_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    rationale: str = ""


class GeneratedTestCase(BaseModel):
    test_id: str
    requirement_ids: List[str] = Field(default_factory=list)
    acceptance_criteria_refs: List[str] = Field(default_factory=list)
    code_refs: List[str] = Field(default_factory=list)
    body: str
    quality_score: Optional[float] = None


class CritiqueResult(BaseModel):
    test_id: str
    score: float
    feedback: str
    revised_body: Optional[str] = None


class TraceabilityEntry(BaseModel):
    requirement_id: str
    test_id: str
    covered_acceptance_criteria: List[str] = Field(default_factory=list)
    confidence: float = 0.0


class GapEntry(BaseModel):
    requirement_id: str
    reason: str
    suggested_followup: str


class EvaluationMetrics(BaseModel):
    correctness_rate: float = 0.0
    requirement_coverage: float = 0.0
    traceability_accuracy: Optional[float] = None
    critique_quality_stats: Dict[str, float] = Field(default_factory=dict)
    cost: Optional[float] = None
    duration_seconds: Optional[float] = None


class ExperimentRunResult(BaseModel):
    model: str
    strategy: str
    context: str
    repeat_index: int
    status: str
    metrics: Optional[EvaluationMetrics] = None
    cost: Optional[float] = None
    duration_seconds: Optional[float] = None
    artifacts: Dict[str, str] = Field(default_factory=dict)
    error: Optional[str] = None


class ProviderConfig(BaseModel):
    name: str
    model: str
    api_base: Optional[str] = None
    api_key_env: Optional[str] = None
    token_price_input: Optional[float] = None
    token_price_output: Optional[float] = None
    enabled: bool = True


class PipelineConfig(BaseModel):
    retries: int = 2
    mapping_confidence_threshold: float = 0.1
    critique_threshold: float = 0.6


class ExperimentsConfig(BaseModel):
    strategies: List[str] = Field(
        default_factory=lambda: ["zero_shot", "few_shot", "chain_of_thought"]
    )
    contexts: List[str] = Field(
        default_factory=lambda: ["code_only", "requirements_only", "requirements_plus_code"]
    )
    repeats: int = 3
    random_seed: int = 42


class IOConfig(BaseModel):
    tests_filename: str = "test_generated.py"
    traceability_filename: str = "traceability.csv"
    gap_report_filename: str = "gap_report.json"


class EvaluationConfig(BaseModel):
    ground_truth_tests: Optional[str] = None


class LLMConfig(BaseModel):
    providers: List[ProviderConfig] = Field(default_factory=list)
    default_provider: str = "mock"


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    experiments: ExperimentsConfig = Field(default_factory=ExperimentsConfig)
    io: IOConfig = Field(default_factory=IOConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)


class GenerationArtifacts(BaseModel):
    requirements: List[Requirement]
    code_elements: List[CodeElement]
    mappings: List[RequirementCodeMapping]
    tests: List[GeneratedTestCase]
    critiques: List[CritiqueResult]
    traceability: List[TraceabilityEntry]
    gaps: List[GapEntry]
    metadata: Dict[str, Any] = Field(default_factory=dict)
