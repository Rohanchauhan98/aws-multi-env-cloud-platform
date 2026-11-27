provider "aws" {
  region = "ap-southeast-2"
}

data "aws_caller_identity" "me" {}

output "role_name" {
  value = regex("assumed-role/([^/]+)", data.aws_caller_identity.me.arn)[0]
}

module "network" {
  source   = "../../modules/network"
  env_name = "dev"
  vpc_cidr = "10.10.0.0/16"

  enable_nat_gateway          = var.enable_nat_gateway
  interface_endpoint_services = var.interface_endpoint_services

  tags = {
    Project   = "multi-env-cloud-platform"
    ManagedBy = "terraform"
  }
}
module "pipeline" {
  source        = "../../modules/pipeline"
  env_name      = "dev"
  force_destroy = true

  tags = {
    Project   = "multi-env-cloud-platform"
    ManagedBy = "terraform"
  }
}