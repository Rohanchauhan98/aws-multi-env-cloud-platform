terraform {
  backend "s3" {
    bucket       = "rohan-tfstate-multienv-34567"
    key          = "dev/terraform.tfstate"
    region       = "ap-southeast-2"
    encrypt      = true
    use_lockfile = true
  }
}