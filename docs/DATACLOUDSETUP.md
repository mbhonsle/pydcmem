# Salesforce Data Cloud Setup for PyDCMem 🚀

> *Transform your existing Data Cloud infrastructure into an intelligent memory powerhouse*

## Prerequisites ✨

PyDCMem leverages your existing **Salesforce Data Cloud** instance as the intelligent backend for memory processing and storage. If you haven't set up Data Cloud yet, don't worry—we've got you covered with the [official Data Cloud setup guide](https://help.salesforce.com/s/articleView?id=data.c360_a_setup_provision.htm&type=5).

### What You'll Need
- ✅ **Salesforce Data Cloud instance** (already provisioned)
- ✅ **Admin access** to your Salesforce org
- ✅ **Connected App** for OAuth authentication
- ✅ **API permissions** for Data Cloud operations

## The PyDCMem Data Flow 🎯

PyDCMem operates through two elegant Data Cloud pathways that work seamlessly with your existing infrastructure:

1. **📥 Write Path**: Streaming Ingestion for real-time memory updates
2. **📤 Read Path**: Search Index Pipeline for intelligent memory retrieval

Let's set up both pathways to unlock the full potential of your AI agents.

## 📥 Write Path: Streaming Ingestion Setup

### The Power of Streaming Memory Updates

PyDCMem harnesses the [Data Cloud Ingestion API](https://developer.salesforce.com/docs/data/data-cloud-int/references/data-cloud-ingestionapi-ref/c360-a-api-get-started.html) to stream memory updates directly into your data lake. This creates a seamless flow where conversations become intelligent memories.

### Step 1: Create the Ingestion Connector

1. **Use the PyDCMem Schema**: When setting up your Ingestion API connector, use the [AIUserAttributesSchema.yml](../src/AIUserAttributesSchema.yml) file. This creates a connector specifically optimized for memory attributes.

2. **Configure Data Objects**: Once your connector is ready, navigate to the Data Cloud App and create the corresponding Datastream, DataLake and Data Model objects.

### Step 2: Authentication Setup

Before diving into the Ingestion API, you'll need a **Connected App** configured for OAuth JWT Bearer authentication. This same app will power both the write and read paths.

### 🎥 Learning Resources

**Video Tutorials:**
- 📺 [Data Cloud Ingestion API Setup](https://www.youtube.com/watch?v=3xWSVGcTORI) - Step-by-step demonstration
- 📺 [Data Cloud Fundamentals & Ingestion API](https://www.youtube.com/watch?v=usfUhzq5kl0) - Comprehensive overview
- 📖 [Official Setup Guide](https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-create-ingestion-data-stream.html)

**Authentication Resources:**
- 🔐 [Salesforce Connected Apps & OAuth Tokens](https://medium.com/@immvbhonsle/salesforce-connected-apps-and-oauth-tokens-729badb30370) - Detailed authentication guide

### 💡 Pro Tips

- **Naming Flexibility**: You can name your connector and objects anything you prefer—just remember to update the corresponding environment variables in PyDCMem
- **Reusable Authentication**: The Connected App you create will serve both ingestion and query operations
- **Schema Optimization**: The provided schema is specifically designed for memory attributes with confidence scoring and metadata support  

## 📤 Read Path: Search Index Pipeline Setup

### Intelligent Memory Retrieval at Scale

PyDCMem leverages Data Cloud's powerful [SQL Query API](https://developer.salesforce.com/docs/data/data-cloud-query-guide/guide/dc-sql-query-apis.html) to perform intelligent memory retrieval. This enables your AI agents to find relevant context in milliseconds, not minutes.

### The three main objects for Memory Storage & Retrieval

PyDCMem queries three specialized Data Cloud objects to deliver intelligent memory experiences:

| Object | Purpose | Creation Method |
|--------|---------|----------------|
| **`AIUserAttributes__dlm`** | 🧠 Main memory repository | Created during Streaming Ingestion setup |
| **`AIUserAttributes_chunk__dlm`** | 🔍 Memory chunk processing | Auto-created with Search Index Pipeline |
| **`AIUserAttributes_index__dlm`** | ⚡ Vector search index | Auto-created with Search Index Pipeline |

> 💡 **Naming Note**: Object names may vary based on your naming conventions—just ensure your environment variables match your actual object names.

### Why Search Index Pipeline?

Since PyDCMem's primary goal is **relevance-based memory retrieval**, we need a sophisticated search pipeline. Data Cloud's [Search Index Pipeline](https://help.salesforce.com/s/articleView?id=data.c360_a_search_index_ground_ai.htm&type=5) provides exactly this capability, enabling:

- **🎯 Semantic Search**: Find memories based on meaning, not just keywords
- **⚡ Vector Similarity**: Leverage AI-powered similarity matching
- **📊 Confidence Scoring**: Rank results by AI confidence levels

### 🎥 Complete Setup Walkthrough

**Video Tutorial**: [Search Index Pipeline Setup](../resources/Search_Index_Setup.mov)

This comprehensive video demonstrates the complete Search Index Pipeline configuration, showing you exactly how to set up the vector search capabilities that power PyDCMem's intelligent memory retrieval.

### The Magic Behind the Scenes ✨

Once both pathways are configured, PyDCMem creates a seamless memory ecosystem:

1. **Conversations** → **AI Extraction** → **Streaming Ingestion** → **Data Lake**
2. **Query Request** → **Search Index** → **Vector Matching** → **Relevant Memories**

This architecture ensures your AI agents always have the right context at the right time, creating truly intelligent conversational experiences.


### Troubleshooting Common Issues

| Issue | Solution |
|-------|----------|
| **Authentication Errors** | Verify your Connected App configuration and JWT Bearer setup |
| **Schema Mismatches** | Ensure your Data Cloud objects match the PyDCMem schema exactly |
| **Search Index Not Working** | Check that the Search Index Pipeline is properly configured and active |
| **Memory Not Retrieving** | Verify your vector index is populated and search queries are formatted correctly |

## 🚀 You're Ready!

Congratulations! You've successfully transformed your Salesforce Data Cloud into an intelligent memory powerhouse. Your AI agents can now:

- **Remember** every conversation detail
- **Learn** from user preferences and context
- **Adapt** to individual user needs
- **Scale** with your enterprise requirements

### Additional Resources

- 📚 [PyDCMem Main Documentation](../README.md)
- 🎥 [Setup Video Tutorials](../resources/)
- 🔗 [Salesforce Data Cloud Documentation](https://www.salesforce.com/data/)
- 💬 [Community Support](https://github.com/mbhonsle/pydcmem/issues)

---

<div align="center">

*Built with the power of Salesforce Data Cloud*

</div>