# 部署指南

## 前置条件

1. **华为云账号**: 已开通 CSS、ModelArts 服务
2. **Python 3.11+**: 建议使用 virtualenv
3. **Terraform**: v1.6+

## 步骤 1: 创建 CSS 集群

```bash
cd infra
cp tfvars.example tfvars.dev
# 编辑 tfvars.dev 配置

terraform init
terraform plan -var-file=tfvars.dev
terraform apply -var-file=tfvars.dev
```

## 步骤 2: 配置环境变量

```bash
# 创建 .env 文件
cp .env.example .env
# 编辑以下变量:
# - HUAWEI_CLOUD_AK
# - HUAWEI_CLOUD_SECRET_KEY
# - CSS_ENDPOINT
# - CSS_USERNAME
# - CSS_PASSWORD
```

## 步骤 3: 安装 Python 依赖

```bash
pip install -r src/requirements.txt
```

## 步骤 4: 加载数据到 CSS

```bash
python src/load-data-to-css.py --recreate 1 --early-stop 1
```

## 步骤 5: 执行 RAG 查询

```bash
python src/ask-huawei-with-rag.py --ask "Your question here"
```

## 清理资源

```bash
cd infra
terraform destroy
```
