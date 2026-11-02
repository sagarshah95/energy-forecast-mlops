# Week 6: private, versioned, encrypted S3 only. No Lambda, SageMaker, or IAM users.
# Review cost and credentials before apply. Empty all versions before destroy.
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
provider "aws" { region = var.aws_region }
variable "aws_region" { type = string; default = "us-east-1" }
variable "bucket_name" { type = string }
resource "aws_s3_bucket" "energy" { bucket = var.bucket_name }
resource "aws_s3_bucket_versioning" "energy" {
  bucket = aws_s3_bucket.energy.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "energy" {
  bucket = aws_s3_bucket.energy.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}
# Block ACLs and policies: either channel can make a bucket public.
resource "aws_s3_bucket_public_access_block" "energy" {
  bucket = aws_s3_bucket.energy.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}
output "bucket_name" { value = aws_s3_bucket.energy.bucket }
