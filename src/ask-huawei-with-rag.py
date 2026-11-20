"""
华为云 RAG 查询脚本
"""
import argparse
import os
import sys
import json
import requests
import numpy as np
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level=os.getenv("LOG_LEVEL", "INFO"))

# 华为云 API 端点
HUAWEI_MODELARTS_URL = os.getenv("HUAWEI_MODELARTS_URL", "")
HUAWEI_EMBEDDING_URL = os.getenv("HUAWEI_EMBEDDING_URL", "")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ask", type=str, default="What is the meaning of <3?",
                        help="Question to ask")
    parser.add_argument("--index", type=str, default="rag",
                        help="CSS index name")
    parser.add_argument("--region", type=str, default="cn-north-4",
                        help="Huawei Cloud region")
    parser.add_argument("--tenant-id", type=str, default=None,
                        help="Filter by tenant ID")
    parser.add_argument("--model-id", type=str, default="moe-bloomz-7b-v1",
                        help="ModelArts model ID")
    parser.add_argument("--embedding-model-id", type=str, default="embedding-002",
                        help="Embedding model ID")
    parser.add_argument("--css-endpoint", type=str, default=None,
                        help="CSS endpoint override")
    parser.add_argument("--css-username", type=str, default="admin",
                        help="CSS username")
    parser.add_argument("--css-password", type=str, default=None,
                        help="CSS password")
    return parser.parse_known_args()


def get_embedding(text: str, region: str = "cn-north-4") -> list:
    """
    调用华为云 ModelArts 获取文本嵌入
    """
    try:
        endpoint = os.getenv("HUAWEI_EMBEDDING_ENDPOINT", "")
        if not endpoint:
            logger.warning("HUAWEI_EMBEDDING_ENDPOINT not set, using random embedding")
            return np.random.rand(768).tolist()

        # 实际 API 调用 (需要添加华为云签名)
        headers = {"Content-Type": "application/json"}
        payload = {"inputs": [text]}

        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("data", [np.random.rand(768).tolist()])[0]
        else:
            logger.warning(f"Embedding API returned {response.status_code}")
            return np.random.rand(768).tolist()
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        return np.random.rand(768).tolist()


def search_similar_docs(endpoint: str, username: str, password: str,
                        index_name: str, query_vector: list,
                        tenant_id: str = None, k: int = 5) -> list:
    """
    使用 kNN 搜索相似文档 (CSS 检索 API)
    """
    url = f"https://{endpoint}:9200/{index_name}/_search"

    # 构建 kNN 查询
    query = {
        "size": k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k": k
                }
            }
        }
    }

    # 添加租户过滤
    if tenant_id:
        query["query"] = {
            "bool": {
                "must": query["query"],
                "filter": {
                    "term": {"tenant_id": tenant_id}
                }
            }
        }

    auth = (username, password)
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=query, auth=auth, headers=headers,
                                 verify=False, timeout=30)
        if response.status_code == 200:
            result = response.json()
            hits = result.get("hits", {}).get("hits", [])
            documents = []
            for hit in hits:
                documents.append({
                    "text": hit["_source"].get("text", ""),
                    "score": hit["_score"]
                })
            return documents
        else:
            logger.error(f"Search failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return []


def call_llm(prompt: str, model_id: str = "moe-bloomz-7b-v1") -> str:
    """
    调用华为云 ModelArts 推理 API
    """
    try:
        endpoint = os.getenv("HUAWEI_MODELARTS_ENDPOINT", "")
        if not endpoint:
            logger.warning("HUAWEI_MODELARTS_ENDPOINT not set, using mock response")
            return "This is a mock response because ModelArts endpoint is not configured."

        # 实际 API 调用 (需要添加华为云签名)
        headers = {"Content-Type": "application/json"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.0,
                "max_tokens": 512
            }
        }

        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result.get("outputs", ["Response received"])[0]
        else:
            logger.warning(f"LLM API returned {response.status_code}")
            return f"Error calling LLM: {response.status_code}"
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return f"Error: {str(e)}"


def create_rag_prompt(question: str, context_docs: list) -> str:
    """
    创建 RAG 提示词
    """
    context = "\n\n".join([f"Context {i+1}:\n{doc['text']}" for i, doc in enumerate(context_docs)])

    prompt = f"""If the context is not relevant, please answer the question by using your own knowledge about the topic. If you don't know the answer, just say that you don't know, don't try to make up an answer. Don't include harmful content.

{context}

Question: {question}
Answer:"""
    return prompt


def main():
    args, _ = parse_args()

    # 从环境变量获取配置
    css_endpoint = args.css_endpoint or os.getenv("CSS_ENDPOINT", "")
    css_username = args.css_username or os.getenv("CSS_USERNAME", "admin")
    css_password = args.css_password or os.getenv("CSS_PASSWORD", "")

    if not css_endpoint:
        logger.error("CSS_ENDPOINT not set. Please provide --css-endpoint or set CSS_ENDPOINT env var")
        sys.exit(1)

    if not css_password:
        logger.error("CSS_PASSWORD not set. Please provide --css-password or set CSS_PASSWORD env var")
        sys.exit(1)

    logger.info(f"Question: {args.ask}")
    logger.info(f"Index: {args.index}")

    # 1. 获取查询的 embedding
    logger.info("Getting query embedding...")
    query_embedding = get_embedding(args.ask, args.region)

    # 2. 搜索相似文档
    logger.info("Searching similar documents in CSS...")
    similar_docs = search_similar_docs(
        css_endpoint, css_username, css_password,
        args.index, query_embedding,
        tenant_id=args.tenant_id
    )

    if not similar_docs:
        logger.warning("No similar documents found, using fallback...")
        similar_docs = [{"text": "No relevant context found."}]

    logger.info(f"Found {len(similar_docs)} similar documents:")
    for i, doc in enumerate(similar_docs):
        logger.info(f"  [{i+1}] Score: {doc.get('score', 0):.4f}")
        logger.info(f"      Text: {doc['text'][:100]}...")

    # 3. 构建 RAG 提示词
    logger.info("Building RAG prompt...")
    rag_prompt = create_rag_prompt(args.ask, similar_docs)

    # 4. 调用 LLM
    logger.info(f"Calling ModelArts LLM ({args.model_id})...")
    response = call_llm(rag_prompt, args.model_id)

    logger.info("")
    logger.info(f"Answer from ModelArts: {response}")


if __name__ == "__main__":
    # 忽略 SSL 警告 (测试环境)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
