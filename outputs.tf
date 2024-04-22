output "lambda_function_name" {
  value       = aws_lambda_function.this.function_name
  description = "The name of the Lambda function."
}

output "lambda_function_arn" {
  value       = aws_lambda_function.this.arn
  description = "The ARN of the Lambda function."
}

output "lambda_layer_version_arn" {
  value       = aws_lambda_layer_version.this.arn
  description = "The ARN of the Lambda layer version."
}

output "iam_role_arn" {
  value       = aws_iam_role.this.arn
  description = "The ARN of the IAM role used by the Lambda function."
}

output "cloudwatch_event_rule_name" {
  value       = var.enable_scheduling ? aws_cloudwatch_event_rule.this[0].name : "Scheduling not enabled"
  description = "The name of the CloudWatch Event Rule. Returns 'Scheduling not enabled' if scheduling is disabled."
}

output "cloudwatch_log_group_name" {
  value       = aws_cloudwatch_log_group.lambda.name
  description = "The name of the CloudWatch Log Group associated with the Lambda function."
}

output "ssm_parameter_slack_token_name" {
  value       = aws_ssm_parameter.slack_token.name
  description = "The name of the SSM parameter that stores the Slack token."
}

output "ssm_parameter_gitlab_token_name" {
  value       = aws_ssm_parameter.gitlab_token.name
  description = "The name of the SSM parameter that stores the GitLab token."
}

output "code_zip_path" {
  value       = data.archive_file.code.output_path
  description = "The path to the zipped code for the Lambda function."
}

output "layer_zip_path" {
  value       = data.archive_file.layer.output_path
  description = "The path to the zipped Lambda layer package."
}
