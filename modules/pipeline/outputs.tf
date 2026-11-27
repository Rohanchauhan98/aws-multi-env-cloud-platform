output "bucket_name" {
  value = aws_s3_bucket.uploads.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.uploads.arn
}

output "queue_url" {
  value = aws_sqs_queue.jobs.id
}

output "queue_arn" {
  value = aws_sqs_queue.jobs.arn
}

output "dlq_arn" {
  value = aws_sqs_queue.dlq.arn
}

output "table_name" {
  value = aws_dynamodb_table.jobs.name
}

output "table_arn" {
  value = aws_dynamodb_table.jobs.arn
}