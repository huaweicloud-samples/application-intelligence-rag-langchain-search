# RAG 使用 LangChain 与华为云 ModelArts + CSS 向量数据库

[English](./README.md)

[![华为云](https://img.shields.io/badge/华为云-CSS-blue)](https://www.huaweicloud.com/product/css.html)
[![ModelArts](https://img.shields.io/badge/华为云-ModelArts-green)](https://www.huaweicloud.com/product/modelarts.html)
[![License](https://img.shields.io/badge/License-MIT--0-blue)](LICENSE)

本项目实现基于 LangChain 的 RAG（检索增强生成）应用，使用华为云 CSS 作为向量数据库存储文档嵌入，使用 ModelArts Studio 作为 LLM 推理服务。通过向量相似度检索增强大语言模型的回答质量。

## 这是什么？

**RAG (Retrieval Augmented Generation)** 是一种结合向量检索与大语言模型的技术：

1. **数据加载**: 将文本文档转换为向量 embeddings，存入 CSS 向量数据库
2. **用户查询**: 用户提出问题，系统从向量数据库中检索相似文档
3. **增强回答**: 将检索到的相关文档作为上下文，结合问题一起发送给 LLM，生成更准确的回答

### 典型应用场景

- 企业内部知识库问答
- 产品文档智能客服
- 技术支持问答系统
- 代码库智能问答

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│                    用户请求                           │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              Python 脚本 (本地运行)                    │
│   - ask-huawei-with-rag.py (RAG 查询)             │
│   - load-data-to-css.py (加载向量数据)              │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┴───────────────┐
        ▼                                 ▼
┌─────────────────────┐      ┌────────────────────────┐
│   ModelArts Studio  │      │   CSS 向量数据库        │
│   (LLM + Embedding)│      │   (CSS 检索引擎 2.x)    │
└─────────────────────┘      └────────────────────────┘
```

## 工作流程

```
1. 加载数据阶段:
   文本数据 → Text Embedding 模型 → 向量 → 存入 CSS

2. 查询阶段:
   用户问题 → Text Embedding 模型 → 向量
   → CSS kNN 检索相似文档
   → 检索结果 + 问题 → LLM
   → 生成回答
```

## 特性

- ✅ **向量搜索**: 使用 CSS 向量检索 API
- ✅ **RAG 检索增强**: LangChain 风格的多文档问答
- ✅ **多租户支持**: 可按 tenant_id 隔离数据
- ✅ **Terraform 部署**: 基础设施即代码
- ✅ **灵活配置**: 支持自定义 Embedding 模型和 LLM

## 前置条件

1. **华为云账号**: 已开通以下服务
   - CSS (Cloud Search Service)
   - ModelArts
   - IAM

2. **工具**
   - Python 3.11+
   - Terraform 1.6+

## 快速开始

### 步骤 1: 部署 CSS 集群

```bash
cd infra
cp tfvars.example tfvars.dev
# 编辑 tfvars.dev 配置

terraform init
terraform plan -var-file=tfvars.dev
terraform apply -var-file=tfvars.dev
```

记录输出的 `css_endpoint`。

### 步骤 2: 配置环境变量

```bash
cd src
cp .env.example .env
# 编辑 .env 填写实际值
```

### 步骤 3: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 4: 加载数据

```bash
python load-data-to-css.py --recreate 1 --early-stop 100
```

### 步骤 5: 执行查询

```bash
python ask-huawei-with-rag.py --ask "How will AI change our daily life?"
```

## 使用方法

### 参数说明

**load-data-to-css.py:**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--recreate` | 0 | 是否重建索引 |
| `--early-stop` | 0 | 早期停止加载文档数 |
| `--index` | rag | 索引名称 |
| `--css-endpoint` | - | CSS 端点 |

**ask-huawei-with-rag.py:**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--ask` | - | 要问的问题 |
| `--index` | rag | 索引名称 |
| `--tenant-id` | - | 租户 ID |
| `--model-id` | moe-bloomz-7b-v1 | 模型 ID |

## 清理资源

```bash
cd infra
terraform destroy
```

## 云服务说明

| 组件 | 说明 |
|------|------|
| CSS | 华为云云搜索服务，提供向量搜索能力 |
| ModelArts | 华为云 AI 开发平台，提供 LLM 推理和 Embedding |

## 许可证

本项目基于 MIT-0 许可证。详情见 [LICENSE](LICENSE) 文件。

## 联系方式

- 问题反馈: [GitHub Issues](https://github.com/huaweicloud-samples/rag-using-langchain-huawei/issues)
