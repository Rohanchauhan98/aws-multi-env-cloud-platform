provider "aws" {
  region = "ap-southeast-2"
}

data "aws_caller_identity" "me" {}

output "role_name" {
  value = regex("assumed-role/([^/]+)", data.aws_caller_identity.me.arn)[0]
}