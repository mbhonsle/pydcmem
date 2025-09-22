# PyDCMem

**Enterprise Agentic Memory implementation based on Salesforce Data Cloud**

PyDCMem is a Python library that provides intelligent memory management for conversational AI systems by extracting, storing, and retrieving user-specific attributes and preferences from natural language conversations using Salesforce Data Cloud as the backend storage.

## Features

- **Intelligent Memory Extraction**: Uses OpenAI's LLM to extract memory-worthy facts from user utterances
- **Data Cloud Integration**: Seamlessly stores and retrieves user attributes using Salesforce Data Cloud
- **Vector Search**: Leverages vector search capabilities for relevant memory retrieval
- **Flexible Context Support**: Handles session variables, dialogue history, and past memory facts
- **Robust Error Handling**: Comprehensive error handling and retry mechanisms
- **CLI Interface**: Command-line interface for testing and integration

## Installation

### Option 1: Install from GitHub (Recommended)

```bash
pip install git+https://github.com/mbhonsle/pydcmem.git
```

### Option 2: Clone and Install Locally

```bash
# Clone the repository
git clone https://github.com/mbhonsle/pydcmem.git
cd pydcmem

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Option 3: Install from Local Source

If you have the source code locally:

```bash
# Navigate to the project directory
cd /path/to/pydcmem

# Install in development mode (recommended for development)
pip install -e .

# Or install normally
pip install .
```

### Development Installation

For development work, install with the `-e` flag to enable editable installs:

```bash
git clone https://github.com/mbhonsle/pydcmem.git
cd pydcmem
pip install -e .
```

This allows you to make changes to the source code without reinstalling the package.

## Quick Start

### Basic Usage

```python
from pydc_mem import MemoryExtractor, UserAttributeClient, AgentMemoryOrchestrator

# Initialize components
extractor = MemoryExtractor()  # Reads OPENAI_API_KEY from environment
ua_client = UserAttributeClient()  # Reads Data Cloud credentials from environment
orchestrator = AgentMemoryOrchestrator(extractor, ua_client)

# Extract and store memories
candidates, report = orchestrator.update(
    user_id="user-123",
    utterance="I usually fly Delta and prefer window seats.",
    session_vars={"passengers": 2, "class": "economy"},
    recent_dialogue=[("Agent", "Do you want Delta again?"), ("User", "Yes, Delta")],
    past_memory_facts=["Home airport = SFO"]
)

print(f"Added: {report.added}, Updated: {report.updated}, Skipped: {report.skipped}")
```

### Command Line Interface

```bash
# Set required environment variables
export OPENAI_API_KEY="sk-..."
export MEMORY_DLO="your_dlo"
export MEMORY_CONNECTOR="your_connector"
export VECTOR_IDX_DLM="your_vector_index"
export CHUNK_DLM="your_chunk_dlm"
export SALESFORCE_ORGANIZATION_ID="your_org_id"

# Extract and store memories
python -m pydc_mem.dcmem --user-id "user-123" --utterance "I prefer morning flights" --op-type update

# Retrieve relevant memories
python -m pydc_mem.dcmem --user-id "user-123" --utterance "What are my preferences?" --op-type get
```

## Architecture

### Core Components

#### 1. MemoryExtractor (`core/memory_extractor.py`)
- **Purpose**: Extracts memory-worthy facts from user utterances using OpenAI's LLM
- **Key Features**:
  - Configurable system prompts for different extraction strategies
  - Support for context variables (session vars, dialogue history, past memories)
  - Pydantic validation for extracted memory candidates
  - JSON parsing with fallback regex extraction

#### 2. UserAttributeClient (`core/memory_client.py`)
- **Purpose**: Manages user attributes in Salesforce Data Cloud
- **Key Features**:
  - CRUD operations for user attributes
  - Vector search for relevant memory retrieval
  - Upsert logic with conflict resolution
  - Comprehensive reporting and error handling

#### 3. AgentMemoryOrchestrator (`dcmem.py`)
- **Purpose**: Orchestrates the end-to-end memory pipeline
- **Key Features**:
  - Coordinates extraction and storage
  - Supports dry-run mode for testing
  - CLI interface for easy integration

### Utility Components

#### 1. DataCloudIngestionClient (`util/ingestion_client.py`)
- Handles data ingestion into Salesforce Data Cloud
- Manages authentication and API communication
- Supports context manager pattern

#### 2. QueryServiceClient (`util/query_svc.py`)
- Executes SQL queries against Data Cloud
- Handles vector search operations
- Manages query result processing

#### 3. MemoryResultsParser (`util/memory_results_parser.py`)
- Parses and normalizes query results
- Handles type coercion for different data types
- Provides clean, structured output format

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | Yes |
| `MEMORY_DLO` | Data Cloud DLO (Data Lake Object) name | Yes |
| `MEMORY_CONNECTOR` | Data Cloud connector API name | Yes |
| `VECTOR_IDX_DLM` | Vector index DLM for search | Yes |
| `CHUNK_DLM` | Chunk DLM for vector search | Yes |
| `SALESFORCE_ORGANIZATION_ID` | Salesforce organization ID | Yes |

### Data Schema

The library uses the `AIUserAttributes` schema defined in `AIUserAttributesSchema.yml`:

```yaml
AIUserAttributes:
  properties:
    tenantId: string
    userId: string
    attribute: string
    value: string
    confidence: number
    source: string
    updatedBy: string
    createdAt: string (date-time)
    lastModifiedAt: string (date-time)
    metadata: string
    id: string
```

## API Reference

### MemoryExtractor

```python
class MemoryExtractor:
    def extract(
        self,
        utterance: str,
        *,
        session_vars: Optional[Dict[str, Any]] = None,
        recent_dialogue: Optional[Sequence[Tuple[str, str]]] = None,
        past_memory_facts: Optional[Iterable[str]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> List[MemoryCandidate]
```

### UserAttributeClient

```python
class UserAttributeClient:
    def fetch_relevant_attributes(self, user_id: str, utterance: str) -> List[Dict]
    def fetch_user_attributes(self, user_id: str) -> List[Dict]
    def upsert_from_candidates(
        self,
        user_id: str,
        candidates: List[MemoryCandidate],
        *,
        normalize_attributes: bool = True,
        case_insensitive_compare: bool = True,
        dedupe_last_write_wins: bool = True,
    ) -> UpsertReport
```

### AgentMemoryOrchestrator

```python
class AgentMemoryOrchestrator:
    def update(
        self,
        *,
        user_id: str,
        utterance: str,
        session_vars: Optional[dict[str, Any]] = None,
        recent_dialogue: Optional[Sequence[Tuple[str, str]]] = None,
        past_memory_facts: Optional[Iterable[str]] = None,
        dry_run: bool = False
    ) -> tuple[List[MemoryCandidate], Optional[UpsertReport]]
    
    def get(self, user_id: str, utterance: str)
```

## Data Models

### MemoryCandidate

```python
class MemoryCandidate(BaseModel):
    entity: str      # User identifier
    attribute: str   # Attribute name (e.g., "preferred_airline")
    value: str       # Attribute value (e.g., "Delta Airlines")
```

### UpsertReport

```python
@dataclass
class UpsertReport:
    user_id: str
    added: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    details: List[UpsertItemResult] = field(default_factory=list)
```

## Advanced Usage

### Custom Memory Extraction

```python
# Custom system prompt for specific use cases
custom_extractor = MemoryExtractor(
    system_instructions="""You are a travel assistant that extracts travel preferences.
    Focus on: airlines, hotels, seating preferences, meal preferences, and travel times.""",
    model="gpt-4o",
    temperature=0.1
)
```

### Batch Processing

```python
# Process multiple utterances
utterances = [
    "I prefer morning flights",
    "I always book window seats",
    "I'm vegetarian, so no meat meals"
]

for utterance in utterances:
    candidates, report = orchestrator.update(
        user_id="user-123",
        utterance=utterance,
        dry_run=False
    )
    print(f"Processed: {len(candidates)} candidates")
```

### Error Handling

```python
try:
    candidates, report = orchestrator.update(
        user_id="user-123",
        utterance="I prefer Delta Airlines"
    )
    
    if report.errors > 0:
        print(f"Errors occurred: {report.errors}")
        for detail in report.details:
            if detail.error:
                print(f"Error in {detail.attribute}: {detail.error}")
                
except Exception as e:
    print(f"Processing failed: {e}")
```

## Development

### Project Structure

```
src/
├── pydc_mem/
│   ├── __init__.py
│   ├── dcmem.py                    # Main orchestrator and CLI
│   ├── core/
│   │   ├── memory_client.py        # Data Cloud client
│   │   └── memory_extractor.py     # LLM-based extraction
│   └── util/
│       ├── ingestion_client.py     # Data Cloud ingestion
│       ├── query_svc.py           # Query service client
│       └── memory_results_parser.py # Result parsing
└── AIUserAttributesSchema.yml      # Data schema definition
```

### Dependencies

- **httpx**: HTTP client for API communication
- **openai**: OpenAI API client for LLM access
- **pydantic**: Data validation and serialization
- **pydc-auth**: Salesforce authentication
- **python-dotenv**: Environment variable management
- **tenacity**: Retry mechanisms
- **cryptography**: Security utilities
- **PyJWT**: JWT token handling
- **uuid6**: UUID generation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- GitHub Issues: [https://github.com/mbhonsle/pydcmem/issues](https://github.com/mbhonsle/pydcmem/issues)
- Documentation: [https://github.com/mbhonsle/pydcmem](https://github.com/mbhonsle/pydcmem)

## Changelog

### v0.1.0
- Initial release
- Core memory extraction and storage functionality
- Data Cloud integration
- CLI interface
- Vector search support
