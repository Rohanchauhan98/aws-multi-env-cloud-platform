variable "env_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "cors_allowed_origins" {
  description = "Origins allowed to POST uploads. Tighten once the frontend URL exists."
  type        = list(string)
  default     = ["*"]
}

variable "retention_days" {
  description = "Days before uploaded files and thumbnails expire."
  type        = number
  default     = 7
}

variable "enable_pitr" {
  description = "Enable DynamoDB point-in-time recovery (billed)."
  type        = bool
  default     = false
}

variable "force_destroy" {
  description = "Allow destroying the bucket while it still holds objects."
  type        = bool
  default     = false
}