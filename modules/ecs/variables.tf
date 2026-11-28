variable "name_prefix" {
  type = string
}

variable "table_arn" {
  type = string
}

variable "bucket_arn" {
  type = string
}

variable "queue_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
variable "region" {
  type    = string
  default = "ap-southeast-2"
}

variable "api_image" {
  type = string
}

variable "worker_image" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "table_name" {
  type = string
}

variable "queue_url" {
  type = string
}

variable "log_retention_days" {
  type    = number
  default = 7
}
variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "api_desired_count" {
  type    = number
  default = 1
}

variable "worker_desired_count" {
  type    = number
  default = 1
}