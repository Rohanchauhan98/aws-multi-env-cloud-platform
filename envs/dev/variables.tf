variable "enable_nat_gateway" {
  type    = bool
  default = false
}

variable "interface_endpoint_services" {
  type    = list(string)
  default = []
}