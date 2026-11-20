variable "region" {
  description = "华为云区域"
  type        = string
  default     = "cn-north-4"
}

variable "project_id" {
  description = "华为云项目ID"
  type        = string
}

variable "name" {
  description = "资源名称前缀"
  type        = string
  default     = "rag-demo"
}

variable "css_version" {
  description = "CSS 版本"
  type        = string
  default     = "2.3.9" # CSS 引擎版本
}

variable "css_instance_type" {
  description = "CSS 实例规格"
  type        = string
  default     = "css.medium" # 2核4G
}

variable "css_node_count" {
  description = "CSS 节点数量"
  type        = number
  default     = 1
}

variable "css_volume_size" {
  description = "CSS 存储大小 (GB)"
  type        = number
  default     = 100
}

variable "css_admin_password" {
  description = "CSS admin 密码"
  type        = string
  sensitive   = true
}

variable "vpc_name" {
  description = "VPC 名称"
  type        = string
  default     = "rag-vpc"
}

variable "vpc_cidr" {
  description = "VPC 网段"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_name" {
  description = "子网名称"
  type        = string
  default     = "rag-subnet"
}

variable "subnet_cidr" {
  description = "子网网段"
  type        = string
  default     = "10.0.0.0/24"
}

variable "access_key" {
  type        = string
  sensitive   = true
  default     = "PLACEHOLDER-YOUR-ACCESS-KEY"
  description = "华为云 AK（生产环境请通过命令行 -var 或环境变量传入，勿写入文件）"
}

variable "secret_key" {
  type        = string
  sensitive   = true
  default     = "PLACEHOLDER-YOUR-SECRET-KEY"
  description = "华为云 SK（生产环境请通过命令行 -var 或环境变量传入，勿写入文件）"
}
