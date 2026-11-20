# RAG using LangChain with Huawei Cloud ModelArts and CSS Vector Database

[中文版](./README.cn.md)

[![Huawei Cloud](https://img.shields.io/badge/Huawei-CSS-blue)](https://www.huaweicloud.com/product/css.html)
[![ModelArts](https://img.shields.io/badge/Huawei-ModelArts-green)](https://www.huaweicloud.com/product/modelarts.html)
[![License](https://img.shields.io/badge/License-MIT--0-blue)](LICENSE)

This project implements a RAG (Retrieval Augmented Generation) application using LangChain, with Huawei Cloud CSS as the vector database for storing document embeddings, and ModelArts Studio as the LLM inference service. It enhances LLM responses through vector similarity retrieval.

## What is this?

**RAG (Retrieval Augmented Generation)** is a technique that combines vector retrieval with large language models:

1. **Data Loading**: Convert text documents into vector embeddings and store them in the CSS vector database
2. **User Query**: User asks a question; the system retrieves similar documents from the vector database
3. **Enhanced Response**: Send retrieved relevant documents as context along with the question to the LLM for more accurate answers

### Typical Use Cases

- Enterprise internal knowledge base Q&A
- Product documentation intelligent customer service
- Technical support Q&A system
- Code repository intelligent Q&A

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    User Request                      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              Python Scripts (Local Run)               │
│   - ask-huawei-with-rag.py (RAG Query)             │
│   - load-data-to-css.py (Load Vector Data)         │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┴───────────────┐
        ▼                                 ▼
┌─────────────────────┐      ┌────────────────────────┐
│   ModelArts Studio  │      │   CSS Vector Database  │
│   (LLM + Embedding)│      │   (CSS Engine 2.x)    │
└─────────────────────┘      └────────────────────────┘
```

## Workflow

```
1. Data Loading Phase:
   Text Data → Text Embedding Model → Vector → Store in CSS

2. Query Phase:
   User Question → Text Embedding Model → Vector
   → CSS kNN Similarity Search
   → Retrieved Documents + Question → LLM
   → Generate Answer
```

## Features

- ✅ **Vector Search**: Using the CSS vector search API
- ✅ **RAG Retrieval**: LangChain-style multi-document Q&A
- ✅ **Multi-tenancy**: Data isolation by tenant_id
- ✅ **Terraform Deployment**: Infrastructure as Code
- ✅ **Flexible Configuration**: Support custom Embedding models and LLMs

## Prerequisites

1. **Huawei Cloud Account**: Services enabled
   - CSS (Cloud Search Service)
   - ModelArts
   - IAM

2. **Tools**
   - Python 3.11+
   - Terraform 1.6+

## Quick Start

### Step 1: Deploy CSS Cluster

```bash
cd infra
cp tfvars.example tfvars.dev
# Edit tfvars.dev with your configuration

terraform init
terraform plan -var-file=tfvars.dev
terraform apply -var-file=tfvars.dev
```

Record the `css_endpoint` from output.

### Step 2: Configure Environment Variables

```bash
cd src
cp .env.example .env
# Edit .env with actual values
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Load Data

```bash
python load-data-to-css.py --recreate 1 --early-stop 100
```

### Step 5: Execute Query

```bash
python ask-huawei-with-rag.py --ask "How will AI change our daily life?"
```

## Usage

### Parameter Reference

**load-data-to-css.py:**

| Parameter | Default | Description |
|----------|---------|-------------|
| `--recreate` | 0 | Recreate index |
| `--early-stop` | 0 | Number of documents to load |
| `--index` | rag | Index name |
| `--css-endpoint` | - | CSS endpoint |

**ask-huawei-with-rag.py:**

| Parameter | Default | Description |
|----------|---------|-------------|
| `--ask` | - | Question to ask |
| `--index` | rag | Index name |
| `--tenant-id` | - | Tenant ID |
| `--model-id` | moe-bloomz-7b-v1 | Model ID |

## Cleanup

```bash
cd infra
terraform destroy
```

## Cloud Services

| Component | Description |
|-----------|-------------|
| CSS | Huawei Cloud Search Service, provides vector search capabilities |
| ModelArts | Huawei Cloud AI development platform, provides LLM inference and Embedding |

## License

This project is licensed under MIT-0. See [LICENSE](LICENSE) file.

## Contact

- Issues: [GitHub Issues](https://github.com/huaweicloud-samples/rag-using-langchain-huawei/issues)
