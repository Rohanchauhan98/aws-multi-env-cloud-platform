output "uploads_bucket" {
  value = module.pipeline.bucket_name
}

output "jobs_queue_url" {
  value = module.pipeline.queue_url
}

output "jobs_table" {
  value = module.pipeline.table_name
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}