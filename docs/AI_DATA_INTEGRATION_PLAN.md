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

## 17. Dataset Arrival Checklist (Saturday)

Upon receiving the dataset, the integration steps must be executed in this exact order:

- [ ] **Step 1: Check File Format**: Identify formats (.csv, .json, .xml).
- [ ] **Step 2: Read Attributes**: Document all columns and fields.
- [ ] **Step 3: Analyze Records Count**: Run record counts.
- [ ] **Step 4: Check Missing Data**: Identify columns containing nulls/blanks.
- [ ] **Step 5: Check Duplicates**: Detect identical rows or duplicate identifiers.
- [ ] **Step 6: Map to Target Model Schema**: Match dataset attributes to the target database columns.
- [ ] **Step 7: Confirm Key Fields**: Identify procedures, eligibility, timelines, fees, and official links.

---

## 18. Risks & Mitigations

- **Risk: Missing URLs or Reference Data**: The dataset might lack official documentation URLs.
  - *Mitigation*: Fallback to the main department portal website URL retrieved from `government_offices` table.
- **Risk: Poor Document Structure**: Unstructured documents might yield low retrieval accuracy.
  - *Mitigation*: Dynamically adjust chunk overlap size and leverage section headers in parent metadata tags.
- **Risk: Vector Store Latency**: Vector similarity search might slow down under large datasets.
  - *Mitigation*: Enable HNSW index structure with optimized index parameters.

---

## 19. Implementation Order

When integration begins, build the systems in this order:
1. **Validation Engine**: Write data ingestion validator schemas.
2. **Ingestion Pipelines**: Implement loaders to insert data into PostgreSQL tables.
3. **Chunking Pipeline**: Set up splitters to populate document chunks.
4. **pgvector Indexing**: Configure the HNSW index structure on the database.
5. **Hybrid Search Service**: Implement reciprocal rank fusion logic in `retrieval_engine.py`.
6. **Agent Wiring**: Integrate hybrid search pipeline into `ResearchAgent`.
7. **RAG Integration**: Integrate context-grounded system prompts in `AdvisoryAgent`.
