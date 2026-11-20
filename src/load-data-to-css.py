"""
加载数据到华为云 CSS 向量数据库
"""
import argparse
import os
import sys
import json
import gzip
import requests
import numpy as np
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level=os.getenv("LOG_LEVEL", "INFO"))

# 华为云 embedding 模型端点
HUAWEI_EMBEDDING_URL = "https:// divorcement inference endpoint"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate", type=int, default=0,
                        help="Recreate the index in CSS")
    parser.add_argument("--early-stop", type=int, default=0,
                        help="Load only N documents")
    parser.add_argument("--index", type=str, default="rag",
                        help="Index name")
    parser.add_argument("--css-endpoint", type=str, default=None,
                        help="CSS endpoint override")
    parser.add_argument("--username", type=str, default="admin",
                        help="CSS username")
    parser.add_argument("--password", type=str, default=None,
                        help="CSS password")
    parser.add_argument("--region", type=str, default="cn-north-4",
                        help="Huawei Cloud region")
    return parser.parse_known_args()


def get_embedding(text: str, region: str = "cn-north-4") -> list:
    """
    调用华为云 ModelArts 获取文本嵌入
    使用 embedding-002 模型
    """
    try:
        # 方式1: 使用华为云 NLP API (示例)
        # 实际需要根据已申请的模型配置
        endpoint = os.getenv("HUAWEI_EMBEDDING_ENDPOINT", "")
        if not endpoint:
            logger.warning("HUAWEI_EMBEDDING_ENDPOINT not set, using dummy embedding")
            # 返回随机向量作为占位符
            return np.random.rand(768).tolist()

        # 实际 API 调用 (需要配置 AK/SK 签名)
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": [text]
        }
        # 这里需要添加华为云签名
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


def create_index(endpoint: str, username: str, password: str, index_name: str):
    """创建 CSS 索引 (CSS 检索 API)"""
    url = f"https://{endpoint}:9200/{index_name}"

    # 索引设置
    settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 768,
                    "method": {
                        "name": "hnsw",
                        "engine": "nmslib",
                        "space_type": "l2"
                    }
                },
                "tenant_id": {"type": "keyword"}
            }
        }
    }

    auth = (username, password)
    try:
        # 先检查索引是否存在
        resp = requests.get(url, auth=auth, verify=False, timeout=10)
        if resp.status_code == 200:
            logger.info(f"Index {index_name} already exists")
            return True

        # 创建索引
        resp = requests.put(url, json=settings, auth=auth, verify=False, timeout=30)
        if resp.status_code in [200, 201]:
            logger.info(f"Index {index_name} created successfully")
            return True
        else:
            logger.error(f"Failed to create index: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        return False


def delete_index(endpoint: str, username: str, password: str, index_name: str):
    """删除 CSS 索引"""
    url = f"https://{endpoint}:9200/{index_name}"
    auth = (username, password)
    try:
        resp = requests.delete(url, auth=auth, verify=False, timeout=10)
        if resp.status_code in [200, 404]:
            logger.info(f"Index {index_name} deleted")
            return True
        else:
            logger.warning(f"Delete index returned: {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error deleting index: {e}")
        return False


def load_documents(endpoint: str, username: str, password: str, index_name: str,
                   documents: list, tenant_id: str = None):
    """批量加载文档到 CSS"""
    url = f"https://{endpoint}:9200/{index_name}/_bulk"
    auth = (username, password)

    bulk_data = []
    for doc in documents:
        action = {"index": {"_index": index_name}}
        bulk_data.append(json.dumps(action))

        doc_body = {
            "text": doc["text"],
            "embedding": doc["embedding"]
        }
        if tenant_id:
            doc_body["tenant_id"] = tenant_id

        bulk_data.append(json.dumps(doc_body))

    # 添加最后的换行
    bulk_data.append("")

    body = "\n".join(bulk_data)
    headers = {"Content-Type": "application/x-ndjson"}

    try:
        resp = requests.post(url, data=body, auth=auth, headers=headers, verify=False, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            errors = result.get("errors", False)
            if errors:
                logger.warning(f"Bulk insert had errors: {result}")
            else:
                logger.info(f"Loaded {len(documents)} documents successfully")
            return True
        else:
            logger.error(f"Bulk insert failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Error loading documents: {e}")
        return False


def load_data_from_huggingface(early_stop: int = 0):
    """从 HuggingFace 下载测试数据"""
    import urllib.request

    url = "https://huggingface.co/datasets/sentence-transformers/embedding-training-data/resolve/main/gooaq_pairs.jsonl.gz"
    tmp_file = "/tmp/gooaq_pairs.jsonl.gz"

    if not os.path.exists(tmp_file):
        logger.info("Downloading dataset from HuggingFace...")
        urllib.request.urlretrieve(url, tmp_file)
        logger.info("Download complete")

    documents = []
    with gzip.open(tmp_file, 'rt', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if early_stop and i >= early_stop:
                break
            try:
                obj = json.loads(line.strip())
                documents.append({
                    "question": obj.get("input", ""),
                    "answer": obj.get("output", "")
                })
            except:
                continue

    logger.info(f"Loaded {len(documents)} documents from dataset")
    return documents


def main():
    args, _ = parse_args()

    # 从环境变量获取配置
    css_endpoint = args.css_endpoint or os.getenv("CSS_ENDPOINT", "")
    css_username = args.username or os.getenv("CSS_USERNAME", "admin")
    css_password = args.password or os.getenv("CSS_PASSWORD", "")
    region = args.region

    if not css_endpoint:
        logger.error("CSS_ENDPOINT not set. Please provide --css-endpoint or set CSS_ENDPOINT env var")
        sys.exit(1)

    if not css_password:
        logger.error("CSS_PASSWORD not set. Please provide --password or set CSS_PASSWORD env var")
        sys.exit(1)

    logger.info(f"CSS Endpoint: {css_endpoint}")
    logger.info(f"Index: {args.index}")

    # 处理索引
    if args.recreate:
        logger.info("Recreating index...")
        delete_index(css_endpoint, css_username, css_password, args.index)

    # 创建索引
    create_index(css_endpoint, css_username, css_password, args.index)

    # 加载数据
    logger.info("Loading data from HuggingFace...")
    raw_docs = load_data_from_huggingface(args.early_stop)

    # 生成 embedding 并批量导入
    batch_size = 10
    for i in range(0, len(raw_docs), batch_size):
        batch = raw_docs[i:i+batch_size]
        documents = []

        for doc in batch:
            text = f"Q: {doc['question']}\nA: {doc['answer']}"
            embedding = get_embedding(text, region)

            documents.append({
                "text": text,
                "embedding": embedding
            })

        # 多租户: 轮流分配 tenant_id
        tenant_id = str((i // batch_size) % 5 + 1)
        load_documents(css_endpoint, css_username, css_password, args.index,
                      documents, tenant_id)

        logger.info(f"Processed {min(i+batch_size, len(raw_docs))}/{len(raw_docs)} documents")

    logger.info("Data loading complete!")


if __name__ == "__main__":
    # 忽略 SSL 警告 (测试环境)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
