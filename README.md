# PyDCMem 🧠✨

**Enterprise Agentic Memory that transforms conversations into intelligent insights**

> *Seamlessly integrate with your existing [Salesforce Data Cloud](https://www.salesforce.com/data/) infrastructure to power next-generation AI agents with persistent, contextual memory.*

## The Challenge We Solve

Imagine your AI agents having the memory of an elephant—remembering every preference, context, and nuance from past conversations. Most Salesforce Enterprise customers have already invested heavily in Data Cloud implementations across their ecosystem. The question is: *How do we provide an Agentic Memory solution for [Salesforce Agentforce](https://www.salesforce.com/agentforce/) that simply plugs into existing Data Cloud infrastructure without requiring custom modifications?*

**PyDCMem answers this elegantly.** 🎯

## What Makes PyDCMem Special

PyDCMem is a sophisticated Python library that transforms raw conversations into intelligent, persistent memory using the power of Salesforce Data Cloud. It's designed for:

- **Salesforce Enterprise Customers & Partners** who want to enhance their AI agents
- **Software Architects** building next-generation conversational systems  
- **Salesforce Admins** seeking seamless integration with existing infrastructure

### The Magic ✨

Instead of building complex custom memory systems, PyDCMem leverages your existing Data Cloud setup through standard **Search Index** and **Streaming Ingestion** pipelines. No custom handling required—just intelligent memory that works.
## Core Capabilities 🚀

### 🧠 **Intelligent Memory Extraction**
- **AI-Powered Insights**: Leverages OpenAI LLMs to extract meaningful facts from conversations, session variables, and dialogue history
- **Semantic Memory Updates**: Automatically updates similar memories with newer, more relevant information
- **Context-Aware Processing**: Understands the full conversation context, not just individual utterances

### ☁️ **Native Data Cloud Integration** 
- **Zero-Copy Architecture**: Works directly with your existing Data Cloud infrastructure
- **Real-Time Processing**: Leverages Data Cloud's streaming ingestion for instant memory updates
- **Vector-Powered Search**: Harnesses Data Cloud's search index pipeline for lightning-fast memory retrieval

### 🎯 **Enterprise-Ready Features**
- **Flexible Context Support**: Handles complex scenarios with session variables, dialogue history, and past memory facts
- **Bulletproof Reliability**: Comprehensive error handling with intelligent retry mechanisms
- **Developer-Friendly**: Clean CLI interface for testing and seamless integration
- **Extensible Design**: Built to support multiple LLM providers (OpenAI ready, others coming soon)

## Quick Start 🏃‍♂️

### Prerequisites
- Python 3.12+
- Salesforce Data Cloud instance
- OpenAI API key

### Installation

**Recommended: Install from GitHub**
```bash
pip install git+https://github.com/mbhonsle/pydcmem.git
```

**For Development:**
```bash
git clone https://github.com/mbhonsle/pydcmem.git
cd pydcmem
pip install -e .
```

> 💡 **Pro Tip**: Use the `-e` flag for development to enable live code changes without reinstalling.

## Usage Examples 💡

### Basic Memory Extraction

```python
from pydc_mem import MemoryExtractor, UserAttributeClient, AgentMemoryOrchestrator

# Initialize the memory system
extractor = MemoryExtractor()  # Reads OPENAI_API_KEY from environment
ua_client = UserAttributeClient()  # Reads Data Cloud credentials from environment
orchestrator = AgentMemoryOrchestrator(extractor, ua_client)

# Transform conversation into intelligent memory
candidates, report = orchestrator.update(
    user_id="user-123",
    utterance="I usually fly Delta and prefer window seats.",
    session_vars={"passengers": 2, "class": "economy"},
    recent_dialogue=[("Agent", "Do you want Delta again?"), ("User", "Yes, Delta")],
    past_memory_facts=["Home airport = SFO"]
)

print(f"✨ Memory Update: {report.added} new, {report.updated} updated, {report.skipped} skipped")
```

### Real-World Scenario: Travel Assistant

```python
# Customer service agent conversation
orchestrator.update(
    user_id="customer-456",
    utterance="I always book business class for international flights, but economy is fine for domestic.",
    session_vars={"trip_type": "international", "budget": "flexible"},
    recent_dialogue=[
        ("Agent", "What's your preferred seating class?"),
        ("User", "It depends on the flight distance")
    ],
    past_memory_facts=["Frequent flyer with United", "Prefers aisle seats"]
)
# Result: Intelligent memory that understands context-dependent preferences
```

### Command Line Interface

```bash
# Configure your environment
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

> 🎯 **CLI Power**: Perfect for testing, debugging, and integration with existing workflows.

## Architecture 🏗️

![PyDcMem.png](resources/PyDcMem.png)

### The Data Cloud Advantage

PyDCMem's architecture is elegantly simple yet powerful, leveraging two core Salesforce Data Cloud processes:

- **🔄 Streaming Ingestion**: Real-time memory updates that flow seamlessly into your data lake
- **🔍 Search Index Pipeline**: Vector-powered search that finds relevant memories in milliseconds

### Why This Matters

Instead of building complex custom infrastructure, PyDCMem works with your existing Data Cloud setup. This means:
- **Zero additional infrastructure costs**
- **Leverages your existing data governance policies**
- **Scales automatically with your Data Cloud instance**
- **Integrates with your existing analytics and reporting**

### Ready to Set Up Data Cloud?

🚀 **[Complete Data Cloud Setup Guide](docs/DATACLOUDSETUP.md)** - Step-by-step instructions to get your memory system running in minutes.

## Configuration ⚙️

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | ✅ Yes | `sk-proj-...` |
| `MEMORY_DLO` | Data Cloud DLO (Data Lake Object) name | ✅ Yes | `AIUserAttributes__dlm` |
| `MEMORY_CONNECTOR` | Data Cloud connector API name | ✅ Yes | `MemoryConnector` |
| `VECTOR_IDX_DLM` | Vector index DLM for search | ✅ Yes | `AIUserAttributes_index__dlm` |
| `CHUNK_DLM` | Chunk DLM for vector search | ✅ Yes | `AIUserAttributes_chunk__dlm` |
| `SALESFORCE_ORGANIZATION_ID` | Salesforce organization ID | ✅ Yes | `00D000000000000EAA` |

> 🔐 **Security Note**: Store these as environment variables or use a secure secrets management system.

### Data Schema

PyDCMem uses a thoughtfully designed schema that captures the essence of intelligent memory:

```yaml
AIUserAttributes:
  properties:
    tenantId: string          # Multi-tenant isolation
    userId: string           # Unique user identifier
    attribute: string        # Memory attribute (e.g., "airline_preference")
    value: string           # The actual memory value
    confidence: number      # AI confidence score (0.0-1.0)
    source: string         # Source of the memory (conversation, profile, etc.)
    updatedBy: string      # System or user that updated the memory
    createdAt: string      # When the memory was first created
    lastModifiedAt: string # When the memory was last updated
    metadata: string       # Additional context and metadata
    id: string            # Unique memory identifier
```

> 📊 **Schema Benefits**: This design enables rich querying, confidence-based filtering, and comprehensive audit trails.

## Advanced Usage 🚀

### Custom Memory Extraction

Tailor PyDCMem to your specific domain with custom extraction logic:

```python
# Travel industry specialization
travel_extractor = MemoryExtractor(
    system_instructions="""You are an expert travel assistant that extracts travel preferences.
    Focus on: airlines, hotels, seating preferences, meal preferences, and travel times.
    Always consider context and user history when extracting preferences.""",
    model="gpt-4o",
    temperature=0.1  # Lower temperature for more consistent extraction
)

# Healthcare domain specialization
healthcare_extractor = MemoryExtractor(
    system_instructions="""You are a healthcare assistant that extracts patient preferences and medical history.
    Focus on: medication preferences, appointment scheduling, communication preferences, and accessibility needs.""",
    model="gpt-4o",
    temperature=0.05  # Very low temperature for medical accuracy
)
```

### Robust Error Handling

```python
try:
    candidates, report = orchestrator.update(
        user_id="user-123",
        utterance="I prefer Delta Airlines"
    )
    
    if report.errors > 0:
        print(f"⚠️  Processing completed with {report.errors} errors")
        for detail in report.details:
            if detail.error:
                print(f"❌ Error in {detail.attribute}: {detail.error}")
    else:
        print(f"✅ Successfully processed {len(candidates)} memory candidates")
                
except Exception as e:
    print(f"💥 Processing failed: {e}")
    # Implement your retry logic or fallback strategy here
```

## Testing & Quality Assurance 🧪

PyDCMem comes with comprehensive testing infrastructure to ensure reliability and performance.

### Quick Test Commands

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all unit tests
pytest

# Run with coverage report
pytest --cov=src/pydc_mem --cov-report=html

# Run integration tests (requires API keys)
pytest -m integration
```

### Advanced Testing Options

**Using the Test Runner:**
```bash
python run_tests.py              # Unit tests only
python run_tests.py integration  # Integration tests
python run_tests.py all          # All tests with coverage
python run_tests.py --install-dev # Install dev deps and test
```

**Using Make Commands:**
```bash
make install-dev    # Install development dependencies
make test-unit      # Run unit tests
make test-integration # Run integration tests  
make test-cov       # Run tests with coverage
make lint           # Run code linting
make format         # Format code
make ci             # Run all CI checks
```

> 🎯 **Testing Philosophy**: Comprehensive unit tests with mocked dependencies, plus integration tests that validate real Data Cloud connectivity.

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Test configuration and fixtures
├── test_memory_extractor.py       # MemoryExtractor tests
├── test_memory_client.py          # UserAttributeClient tests
├── test_orchestrator.py           # AgentMemoryOrchestrator tests
└── test_utilities.py              # Utility classes tests
```

### Test Categories

- **🧪 Unit Tests**: Test individual components in isolation with mocked dependencies
- **🔗 Integration Tests**: Validate real Data Cloud connectivity and end-to-end workflows
- **📊 Performance Tests**: Ensure memory operations scale efficiently
- **🛡️ Security Tests**: Validate authentication and data protection mechanisms

## Development 👨‍💻

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

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **HTTP Client** | `httpx` | High-performance async HTTP requests |
| **AI/LLM** | `openai` | GPT-4 powered memory extraction |
| **Data Validation** | `pydantic` | Type-safe data models and validation |
| **Authentication** | `pydc-auth` | Salesforce OAuth and JWT handling |
| **Configuration** | `python-dotenv` | Environment variable management |
| **Resilience** | `tenacity` | Intelligent retry mechanisms |
| **Security** | `cryptography` | Encryption and security utilities |
| **Tokens** | `PyJWT` | JWT token parsing and validation |
| **IDs** | `uuid6` | Time-ordered unique identifiers |

> 🏗️ **Architecture Note**: Clean separation of concerns with dedicated modules for extraction, storage, and orchestration.

## Contributing 🤝

We welcome contributions from the community! Here's how you can help:

1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **💻 Make** your changes with tests
4. **✅ Run** the test suite (`make ci`)
5. **📝 Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **🚀 Push** to your branch (`git push origin feature/amazing-feature`)
7. **🔀 Open** a Pull Request

### Contribution Guidelines
- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting

## License 📄

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## Support & Community 💬

### Getting Help
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/mbhonsle/pydcmem/issues)
- **📚 Documentation**: [Project Repository](https://github.com/mbhonsle/pydcmem)
- **💡 Feature Requests**: Open an issue with the `enhancement` label

### Community Resources
- **📖 Data Cloud Setup**: [Complete Setup Guide](docs/DATACLOUDSETUP.md)
- **🎥 Video Tutorials**: Check the `resources/` directory for setup videos
- **🔗 Salesforce Data Cloud**: [Official Documentation](https://www.salesforce.com/data/)

## Changelog 📋

### v0.1.0 - Initial Release
- ✨ **Core Features**: Memory extraction and storage functionality
- ☁️ **Data Cloud Integration**: Seamless Salesforce Data Cloud connectivity
- 🖥️ **CLI Interface**: Command-line tools for testing and integration
- 🔍 **Vector Search**: High-performance memory retrieval
- 🧪 **Testing Suite**: Comprehensive unit and integration tests
- 📚 **Documentation**: Complete setup and usage guides

---

<div align="center">

**Built with ❤️ for the Salesforce ecosystem**

*Transform your AI agents with intelligent, persistent memory*

</div>
