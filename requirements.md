# ReqLens — Software Requirements

## 1. Overview

ReqLens is a Python CLI tool that generates unit tests from both software requirements and source code using LLMs. It differentiates itself from existing tools (Copilot, ChatGPT) by accepting requirements as additional context, ensuring every generated test is explicitly linked to the requirement it validates. The tool produces test files, a traceability matrix, and a gap report identifying requirements lacking test coverage.

---

## 2. Functional Requirements

### 2.1 Pipeline Architecture

The core system is a five-step LangChain pipeline.

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-P1 | Requirements Parsing | Parse raw requirements from markdown, text, or CSV into structured objects containing IDs, acceptance criteria, priorities, and dependencies. |
| FR-P2 | Code Analysis | Analyze Python source code to identify functions, classes, and methods with their signatures and complexity metrics. |
| FR-P3 | Requirement-to-Code Mapping | Map each parsed requirement to the code elements that implement it, assigning a confidence score to each mapping. |
| FR-P4 | Test Generation | Generate pytest test cases for each requirement-code mapping. Each test must explicitly reference the requirement ID and acceptance criteria it covers. |
| FR-P5 | Self-Critique & Revision | Review generated tests for correctness, quality, and requirement coverage. Score each test and optionally revise low-quality ones. |

### 2.2 CLI Commands

| ID | Command | Description |
|----|---------|-------------|
| FR-C1 | `generate` | Run the full five-step pipeline on a given requirements file and code directory. Produce test files, a traceability matrix, and a gap report. |
| FR-C2 | `evaluate` | Compare generated tests against human-written ground truth tests. Measure correctness, coverage, and traceability accuracy. |
| FR-C3 | `experiment` | Run the full 3×3 matrix (3 prompt strategies × 3 input contexts) across multiple models with repeated runs for statistical significance. |
| FR-C4 | `report` | Produce human-readable summaries from experiment data. |

### 2.3 Prompt Strategies

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-S1 | Zero-Shot Prompting | Support generating tests with no examples in the prompt. |
| FR-S2 | Few-Shot Prompting | Support generating tests with example test cases included in the prompt. |
| FR-S3 | Chain-of-Thought Prompting | Support generating tests with step-by-step reasoning in the prompt. |

### 2.4 Input Contexts

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-I1 | Code-Only | Generate tests using only source code as input (no requirements). |
| FR-I2 | Requirements-Only | Generate tests using only requirements as input (no source code). |
| FR-I3 | Requirements-Plus-Code | Generate tests using both requirements and source code as input. |

### 2.5 LLM Provider Support

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-L1 | Multi-Provider Support | Support multiple LLM providers, including Claude and GPT-4o, selectable via configuration. |

### 2.6 Output Artifacts

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-O1 | Test Files | Generate valid pytest test files that can be executed directly. |
| FR-O2 | Traceability Matrix | Produce a matrix linking each generated test to the requirement it validates. |
| FR-O3 | Gap Report | Produce a report identifying requirements that lack test coverage. |

---

## 3. Non-Functional Requirements

### 3.1 Data Validation

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-D1 | Pydantic Models | Use Pydantic for structured validation across all pipeline stages — requirements, code elements, mappings, test cases, critique results, traceability entries, and gap reports. |

### 3.2 Configuration

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-CF1 | YAML Configuration | Externalize all configuration to YAML files covering LLM settings, pipeline behavior, input/output formats, and evaluation parameters. |

### 3.3 Error Handling

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-E1 | LLM Failure Handling | Handle rate limits, context window overflow, and invalid/malformed LLM output gracefully. |
| NFR-E2 | Input Error Handling | Handle missing files, unsupported formats, and malformed input with clear error messages. |
| NFR-E3 | Pipeline Failure Handling | Handle failures at each pipeline step independently, providing actionable diagnostics. |

### 3.4 Scope Constraints

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-SC1 | Python Only | Support only Python source code as input. |
| NFR-SC2 | Pytest Output | Generate only pytest-compatible test files. |
| NFR-SC3 | CLI Interaction | All user interaction is via CLI (no GUI or web interface). |

---

## 4. Research / Evaluation Requirements

### 4.1 Experiment Design

| ID | Requirement | Description |
|----|-------------|-------------|
| RR-E1 | 3×3 Experiment Matrix | Support running all 9 configurations (3 prompt strategies × 3 input contexts) per model. |
| RR-E2 | Repeated Runs | Each configuration must be repeated at least 3 times for statistical significance. |
| RR-E3 | Multi-Model Comparison | Support running experiments across multiple LLM providers in a single experiment session. |

### 4.2 Metrics

| ID | Requirement | Description |
|----|-------------|-------------|
| RR-M1 | Test Correctness Rate | Measure the percentage of generated tests that pass when executed. |
| RR-M2 | Requirement Coverage | Measure the percentage of requirements that have at least one corresponding test. |
| RR-M3 | Traceability Accuracy | Measure correctness of the requirement-to-test linkages against ground truth. |
| RR-M4 | Quality Scores | Capture quality scores from the self-critique pipeline step. |
| RR-M5 | Cost Tracking | Track LLM API cost per generation run. |
| RR-M6 | Time Tracking | Track wall-clock time per generation run. |

### 4.3 Benchmarks

| ID | Requirement | Description |
|----|-------------|-------------|
| RR-B1 | Benchmark Projects | Use selected open-source Python projects with documented requirements and existing test suites as ground truth. |

### 4.4 Statistical Analysis

| ID | Requirement | Description |
|----|-------------|-------------|
| RR-S1 | Paired Statistical Tests | Use paired tests and effect sizes to determine whether providing requirements context produces significantly better tests than code-only generation. |

---

## 5. Team & Timeline

### 5.1 Team Responsibilities

| Member | Responsibility |
|--------|---------------|
| Sriman | Pipeline architecture and integration |
| Vamsi | Prompt engineering and benchmarks |
| Varun | Evaluation and statistical analysis |

### 5.2 Milestones

| Milestone | Target |
|-----------|--------|
| Project start | Week 5 |
| Working prototype | Week 8 |
| Experiments running | Weeks 11–12 |
| Project completion | Week 14 |
