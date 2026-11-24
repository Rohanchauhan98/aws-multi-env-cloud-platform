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
variable "enable_nat_gateway" {
  description = "Create a single shared NAT gateway for private subnets. Billed hourly."
  type        = bool
  default     = false
}

variable "interface_endpoint_services" {
  description = "Interface endpoint service suffixes, e.g. [\"ecr.api\", \"ecr.dkr\", \"logs\", \"secretsmanager\"]. Billed hourly per AZ."
  type        = list(string)
  default     = []
}