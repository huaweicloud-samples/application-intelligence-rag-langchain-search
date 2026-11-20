terraform {
  required_version = ">= 1.6"

  required_providers {
    huaweicloud = {
      source = "huaweicloud/huaweicloud"
    }
  }
}

# 本地值
locals {
  project_id = var.project_id != "" ? var.project_id : data.huaweicloud_identity_projects.project.projects[0].id
}

# 数据依赖
data "huaweicloud_identity_projects" "project" {
  name = var.region
}

# VPC 网络
resource "huaweicloud_vpc" "vpc" {
  name = var.vpc_name
  cidr = var.vpc_cidr
}

# 子网
resource "huaweicloud_vpc_subnet" "subnet" {
  name       = var.subnet_name
  vpc_id     = huaweicloud_vpc.vpc.id
  cidr       = var.subnet_cidr
  gateway_ip = cidrhost(var.subnet_cidr, 1)
}

# 安全组
resource "huaweicloud_networking_secgroup" "sg" {
  name        = "${var.name}-sg"
  description = "Security group for RAG demo"
}

# 输出
output "vpc_id" {
  description = "VPC ID"
  value       = huaweicloud_vpc.vpc.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = huaweicloud_vpc_subnet.subnet.id
}

output "security_group_id" {
  description = "Security Group ID"
  value       = huaweicloud_networking_secgroup.sg.id
}
