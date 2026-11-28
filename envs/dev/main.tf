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

module "ecr" {
  source       = "../../modules/ecr"
  name_prefix  = "dev"
  force_delete = true
}
module "ecs" {
  source = "../../modules/ecs"

  name_prefix = "dev"

  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids

  table_arn   = module.pipeline.table_arn
  table_name  = module.pipeline.table_name
  bucket_arn  = module.pipeline.bucket_arn
  bucket_name = module.pipeline.bucket_name
  queue_arn   = module.pipeline.queue_arn
  queue_url   = module.pipeline.queue_url

  api_image    = "${module.ecr.repository_urls["api"]}:f32d5f4"
  worker_image = "${module.ecr.repository_urls["worker"]}:f32d5f4"

  tags = {
    Project   = "multi-env-cloud-platform"
    ManagedBy = "terraform"
  }
}