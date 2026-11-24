variable "env_name" {
  description = "Environment name, used in resource names and tags."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
}

variable "az_count" {
  description = "Number of Availability Zones to use."
  type        = number
  default     = 2
}

variable "tags" {
  description = "Extra tags applied to all resources."
  type        = map(string)
  default     = {}
}