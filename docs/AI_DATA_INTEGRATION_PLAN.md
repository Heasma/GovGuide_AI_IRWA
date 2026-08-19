# GovGuide AI — Technical Design and Implementation Plan: AI & Data Integration Phase

---

## 1. Current Architecture Overview

The system uses a clean MVC and multi-agent orchestration architecture to separate infrastructure, business rules, persistence, and AI reasoning.

### 1.1 MVC Flow (General Workflows)
```
[Client / UI]
     │ (HTTP Request)
     ▼
[Controller] (app/controllers/) — Handles routing, validation, status codes
     │
     ▼
[Service] (app/services/) — Handles transaction coordination, business logic
     │
     ▼
[Repository] (app/repositories/) — Handles database CRUD operations (SQLAlchemy)
     │
     ▼
[Model] (app/models/) — Declarative tables (Base metadata)
     │
     ▼
[Database] (PostgreSQL 17 / pgvector)
```

### 1.2 AI Query Request Flow
```
[Client / UI]
     │ (QueryRequest)
     ▼
[QueryController]
     │
     ▼
[QueryService]
     │
     ▼
[Orchestrator] (app/orchestrator/)
     │
     ├─► [ResearchAgent] (app/agents/research_agent/)
     │         │
     │         ▼
     │   [NLP & Retrieval] (app/nlp/ & app/retrieval/)
     │         │ (EvidenceBundle)
     │         ▼
     ├─► [AdvisoryAgent] (app/agents/advisory_agent/)
     │         │ (Generative RAG)
     │         ▼
     ├─► [Responsible AI / Guardrails] (app/responsible_ai/)
     │
     ▼
[QueryResponse]
```

---

## 2. Ingestion Architecture

Ingestion must be designed as an offline/background pipeline that takes the raw government dataset and imports it into the system without blocking production transactions.

```
                  +--------------------------------+
                  |  Raw Government Dataset File   |
                  +--------------------------------+
                                  │
                                  ▼
                  +--------------------------------+
                  |    Schema Detection Stage      |
                  | (CSV/JSON/XML format & columns)|
                  +--------------------------------+
                                  │
                                  ▼
                  +--------------------------------+
                  |      Validation Engine         |
                  |  (Pydantic Type & Rules Check) |
                  +--------------------------------+
                                  │
                                  ▼
                  +--------------------------------+
                  |     Data Normalization Layer   |
                  |  (String cleaning, UTC dates)  |
                  +--------------------------------+
                                  │
                                  ▼
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
+------------------+                              +------------------+
| Relational Load  |                              |  RAG Prep Pipeline|
| (Offices/Services|                              | (Text Chunking)  |
| PostgreSQL tables|                              +------------------+
+------------------+                                       │
                                                           ▼
                                                  +------------------+
                                                  | Embedding Gen    |
                                                  | (async batching) |
                                                  +------------------+
                                                           │
                                                           ▼
                                                  +------------------+
                                                  | Vector + BM25    |
                                                  | Indexes Loading  |
                                                  +------------------+
```

---

## 3. Data Pipeline Implementation

The data pipeline consists of two parallel processing phases: Relational Storage and Search Indexing.

### 3.1 Pipeline Stages
1. **Extract**: Stream or read the raw files (CSV, JSON, or XML) to minimize memory usage.
2. **Transform / Clean**:
   - Strip leading/trailing whitespaces from strings.
   - Detect and convert timestamps to UTC timezone-aware objects.
   - Extract raw metadata into JSONB format to preserve secondary attributes.
3. **Load (Relational)**:
   - Insert entries into the `government_offices` table.
   - Resolve relationships and insert mapped services into `government_services` with foreign keys.
4. **Load (Search)**:
   - Extract raw text documents, partition them into chunks, and persist them in the `document_chunks` table.
   - Run asynchronous batch calls to the embedding model to populate vector embeddings.

---

## 4. Ingestion Validation Strategy

To prevent corrupt, partial, or malformed data from reaching the production tables, we will enforce strict programmatic checks:

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any

class RawServiceValidationSchema(BaseModel):
    service_code: str = Field(min_length=1)
    name: str = Field(min_length=3, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None
    office_name: str = Field(min_length=1)
    source_url: Optional[HttpUrl] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 4.1 Validation Execution Rules:
- **Format Verification**: Reject files that fail basic parser checks (e.g., malformed JSON or unescaped CSVs).
- **Rule Enforcement**:
  - Uniqueness: Enforce unique constraints on `service_code`.
  - Integrity: Ensure each service is linked to a valid office.
- **Reporting**: Log all rejected records with reason details to a pipeline validation report file (`data_validation_report.json`).

---

## 5. Dataset-to-Model Mapping Strategy

This mapping defines how raw attributes map to target database columns.

| Target Model Field | Mapped Dataset Source Attribute | Transformation Rule | Status |
| :--- | :--- | :--- | :--- |
| `GovernmentOffice.name` | `office_name` or `ministry` | Trim whitespace | **AVAILABLE** |
| `GovernmentOffice.department`| `sub_department` or `branch` | Fallback to `None` if blank | **AVAILABLE** |
| `GovernmentService.service_code`| `service_id` or `code` | Format as uppercase slug | **AVAILABLE** |
| `GovernmentService.name` | `service_name` or `title` | Trim whitespace | **AVAILABLE** |
| `GovernmentService.category` | `service_category` | Standardize lower-case categories | **DERIVED** |
| `OfficialSource.checksum` | File contents hash | SHA-256 calculation | **DERIVED** |
| `OfficialSource.raw_content` | Raw file text | Full text extraction | **AVAILABLE** |
| `DocumentChunk.token_count` | Chunk text | Compute using tiktoken | **DERIVED** |
| `DocumentChunk.embedding` | Chunk text | API Embeddings Call | **DERIVED** (Saturday) |
| `GovernmentService.fees` | `fee_amount` or `charges` | Unify currency representation | **UNKNOWN** |

---

## 6. Chunking Strategy

For high RAG accuracy, raw source documents must be chunked appropriately before indexing:

- **Method**: Recursive Character Text Splitter.
- **Chunk Size**: Target `500` tokens (balances retrieval granularity and LLM context window).
- **Overlap**: `50` tokens (preserves context at chunk boundaries).
- **Metadata Tagging**: Each chunk stored in `document_chunks` must retain:
  - `source_id`: UUID reference to parent source.
  - `service_id`: UUID reference to the associated service.
  - `chunk_index`: Integer index of chunk sequence.
  - `metadata`: JSONB containing category, title, and section headers to support precise SQL metadata filtering.

---

## 7. BM25 Architecture

- **Search Engine**: PostgreSQL Full-Text Search (using `tsvector` and `tsquery`) to eliminate external infra dependency.
- **Indexed Fields**: `name`, `description`, and `category` from `government_services`, alongside `content` in `document_chunks`.
- **Lexical Processor**: English stemmer with standard stopwords removed.
- **Column setup**:
  - Add `tsvector` columns to `government_services` and `document_chunks`.
  - Create `GIN` indexes on the `tsvector` columns for fast lexical searches.

---

## 8. Vector Retrieval Architecture

- **Embedding Model**: OpenAI `text-embedding-3-small` (1536 dimensions) or standard open-source alternative.
- **Vector Engine**: `pgvector` extension configured in PostgreSQL.
- **Table Definition Update**:
  - Future Alembic migration to add the embedding column:
    ```sql
    ALTER TABLE document_chunks ADD COLUMN embedding VECTOR(1536);
    ```
- **Vector Index**: `HNSW` (Hierarchical Navigable Small World) index using Cosine Distance (`vector_cosine_ops`) for sub-millisecond retrieval speeds.

---

## 9. Hybrid Retrieval Architecture

To combine lexical and semantic retrieval capabilities, we will use a Hybrid Search pattern:

```
                  +--------------------------------+
                  |          User Query            |
                  +--------------------------------+
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
   +---------------------------+     +---------------------------+
   |   BM25 Lexical Search     |     |   Semantic Vector Search  |
   |   (PostgreSQL tsquery)    |     |    (pgvector Cosine Sim)  |
   +---------------------------+     +---------------------------+
                 │                                 │
                 │ (List of DocumentChunks)        │ (List of DocumentChunks)
                 └────────────────┬────────────────┘
                                  ▼
   +-------------------------------------------------------------+
   |             Reciprocal Rank Fusion (RRF) Stage              |
   |      Score = Sum( 1 / (60 + rank_bm25), 1 / (60 + rank_v) ) |
   +-------------------------------------------------------------+
                                  │
                                  ▼
   +-------------------------------------------------------------+
   |                  RRF Rank Sorted Results                    |
   +-------------------------------------------------------------+
```

---

## 10. Reranking Architecture

- **Model**: Local or API Cross-Encoder (e.g., `bge-reranker-base`).
- **Processing Stage**: Post-retrieval reranking.
- **Execution Flow**:
  1. Retrieve top-20 chunks using the Hybrid Search pipeline.
  2. Format inputs: `[[query, chunk_1_text], [query, chunk_2_text], ...]`
  3. Run inference on the Reranker to calculate semantic relevance scores.
  4. Retain top-k (e.g., top-5) chunks to construct the final prompt context.

---

## 11. EvidenceBundle Structure

The `EvidenceBundle` holds retrieval outputs sent from the `ResearchAgent` to the `AdvisoryAgent`:

```python
class SourceReference(BaseModel):
    source_id: str
    title: str
    url: Optional[str]
    excerpt: str

class EvidenceResult(BaseModel):
    chunk_id: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any]

class EvidenceBundle(BaseModel):
    query: str
    intent: str
    sufficient: bool
    confidence_score: float
    sources: List[SourceReference]
    chunks: List[EvidenceResult]
    caveats: List[str]
```

---

## 12. Research Agent Workflow

1. **Query Parsing & Safety Check**: Analyze query via `IntentClassifier`, and assert prompt safety via `PromptInjectionGuard`.
2. **Metadata Extraction**: Parse query entities (e.g., locations, office names) to extract database metadata filter terms.
3. **Execution**: Execute the Hybrid Search pipeline (BM25 + pgvector Vector + Reranking).
4. **Sufficiency Audit**:
   - If maximum reranker score is below `0.45` or zero chunks return, mark `sufficient = False`.
   - Else, construct `EvidenceBundle` containing top-k chunks.

---

## 13. Advisory Agent Workflow

1. **State Inspection**: Inspect `EvidenceBundle.sufficient`. If `False`, respond with a standard, safe insufficient-evidence statement.
2. **Context Compilation**: Format the retrieved chunk texts into a system context block.
3. **Inference**: Pass the compiled context, query, and system guidelines to the LLM.
4. **Output Construction**: Ensure the model references citations strictly from the provided source urls.

---

## 14. Grounded RAG Prompt Design

```
System Prompt:
You are GovGuide AI, an agentic assistant for government service discovery.
Your task is to answer the user's query using ONLY the provided evidence.

Evidence Context:
[START EVIDENCE]
{{ FOR CHUNK IN EVIDENCE_CHUNKS }}
Source: {{ CHUNK.title }} | URL: {{ CHUNK.url }}
Content: {{ CHUNK.content }}
---
{{ ENDFOR }}
[END EVIDENCE]

Instructions:
1. Base your answer strictly on the provided evidence.
2. Cite sources using matching URLs from the evidence context (e.g., "[Source Title](URL)").
3. If the evidence does not contain sufficient details to answer the query, state:
   "I cannot find sufficient official information in the database to answer this query."
   Do NOT make up or extrapolate instructions, fees, or timelines.
```

---

## 15. Responsible AI Controls

- **Hallucination Prevention**: System prompt restricts response construction strictly to provided context.
- **Safety Assertions**: Incoming queries must clear the `PromptInjectionGuard`.
- **Verification Hook**: An automatic post-generation check asserts that the response does not contain external URLs, unverified procedures, or terms absent from the retrieved context.

---

## 16. Evaluation Methodology

```
                          ┌──────────────────────────┐
                          │    System Evaluation     │
                          └─────────────┬────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
+---------------------+      +---------------------+      +---------------------+
|   Retrieval Quality |      |   Generation Check  |      |   Latency & SLA     |
|  - Precision @ k    |      |  - Groundedness     |      |  - Chunk retrieval  |
|  - Recall @ k       |      |  - Citation accuracy|      |  - Reranker inference|
|  - MRR / MAP        |      |  - Hallucination %  |      |  - LLM response     |
+---------------------+      +---------------------+      +---------------------+
```

- **Groundedness Scoring**: Evaluated using LLM-as-a-judge by checking if all output claims are entailed by the input context.
- **Intent Accuracy**: Monitored using a test set of common queries mapped to predefined service categories.

---

## 17. Dataset Arrival Checklist — COMPLETED 2026-08-19

Dataset received and profiled. All checklist items completed.

- [x] **Step 1: Check File Format**: CSV, UTF-8-SIG encoding, comma delimiter.
- [x] **Step 2: Read Attributes**: 37 columns confirmed. See `data/validation/dataset_profile.json`.
- [x] **Step 3: Analyze Records Count**: **53,091 rows** confirmed.
- [x] **Step 4: Check Missing Data**: Key findings — `LICENSE STATUS CHANGE DATE` is 100% NULL; `APPLICATION CREATED DATE` is 78.9% NULL; `SSA` is 73.6% NULL. See `data/validation/missing_values.csv`.
- [x] **Step 5: Check Duplicates**: 0 complete duplicate rows. 871 LICENSE NUMBERs appear on multiple records (renewal cycles expected). 7,477 ACCOUNT NUMBERs appear on multiple records (one business, multiple licenses — expected). See `data/validation/duplicate_summary.csv`.
- [x] **Step 6: Map to Target Model Schema**: Full mapping proposal in `data/validation/dataset_model_mapping.md`. Key semantic mismatch: dataset describes licensed businesses, not government offices.
- [x] **Step 7: Confirm Key Fields**: Procedures, eligibility, fees, official URLs, and contact info are **NOT present** in the dataset. Supplementary BACP data required. See `data/validation/missing_project_attributes.md` and `data/validation/gs_office_additional_data_requirements.md`.

---

## 18. Risks & Mitigations

- **Risk: Missing URLs or Reference Data**: The dataset lacks official documentation URLs entirely.
  - *Mitigation*: Collect BACP official URLs per license type (56 types) as OfficialSource records.
- **Risk: Dataset Describes Businesses, Not Government Services**: The primary entity is a licensed business, not a service.
  - *Mitigation*: Use LICENSE CODE + LICENSE DESCRIPTION as the GovernmentService entity; use BACP supplementary data for procedural content.
- **Risk: APPLICATION CREATED DATE 78.9% Missing**: Processing time cannot be reliably computed from dataset alone.
  - *Mitigation*: Collect official BACP processing time estimates from BACP website per license type.
- **Risk: Poor Document Structure**: BUSINESS ACTIVITY field contains pipe-delimited multi-value text.
  - *Mitigation*: Split on " | " delimiter during transformation; index each activity separately.
- **Risk: LICENSE STATUS CHANGE DATE 100% NULL**: Status change tracking unavailable.
  - *Mitigation*: Omit this field from ingestion; rely on LICENSE STATUS (currently all "AAI") and temporal fields.
- **Risk: Vector Store Latency**: Vector similarity search might slow down under large datasets.
  - *Mitigation*: Enable HNSW index structure with optimized index parameters.

---

## 19. Implementation Order

When integration begins, build the systems in this order:
1. **Supplementary Data Collection**: Collect BACP procedural data (fees, eligibility, procedures, URLs) for all 56 license types.
2. **Validation Engine**: Write data ingestion validator schemas (Pydantic) for both CSV and supplementary data.
3. **Ingestion Pipelines**: Implement loaders to insert data into PostgreSQL tables.
4. **Chunking Pipeline**: Set up splitters to populate document chunks from BUSINESS ACTIVITY + supplementary BACP text.
5. **pgvector Indexing**: Configure the HNSW index structure on the database.
6. **Hybrid Search Service**: Implement reciprocal rank fusion logic in `retrieval_engine.py`.
7. **Agent Wiring**: Integrate hybrid search pipeline into `ResearchAgent`.
8. **RAG Integration**: Integrate context-grounded system prompts in `AdvisoryAgent`.

---

## 20. Phase 1 Profiling — Confirmed Dataset Facts (2026-08-19)

| Property | Value |
|----------|-------|
| Dataset file | `Business_Licenses_-_Current_Active_20260819.csv` |
| Rows | 53,091 |
| Columns | 37 |
| Encoding | UTF-8-SIG |
| Delimiter | Comma `,` |
| SHA-256 | `d3246a6657fe8cbb46a12a5fc6027569d2ca783ab4b7040449eac4dfaa564a41` |
| Complete duplicate rows | 0 |
| LICENSE STATUS unique values | 1 (AAI only — all records are active) |
| License types (LICENSE DESCRIPTION) | 56 unique types |
| Unique business accounts | 36,262 |
| Date columns | 9 (8 parseable; LICENSE STATUS CHANGE DATE = 100% NULL) |
| Location columns | 15 |
| Lat/Lon coverage | ~92% of records geocoded |
| Geography | Chicago, IL (CITY: 951 unique values; STATE: 48 unique values) |
| Profiling script | `data/profiling/profile_dataset.py` |
| Profiling outputs | `data/validation/` (6 files) |
