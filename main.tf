locals {
  layer_description                      = var.layer_description == null ? "Used by Lambda function '${var.function_name}'." : var.layer_description
  role_description                       = var.role_description == null ? "Used by Lambda function '${var.function_name}'." : var.role_description
  cloudwatch_event_rule_description      = var.cloudwatch_event_rule_description == null ? "Used by Lambda function '${var.function_name}'." : var.cloudwatch_event_rule_description
  ssm_parameter_slack_token_name         = var.ssm_parameter_slack_token_name == null ? "/${var.function_name}/slack-token" : var.ssm_parameter_slack_token_name
  ssm_parameter_slack_token_description  = var.ssm_parameter_slack_token_description == null ? "Slack token for Lambda function '${var.function_name}'." : var.ssm_parameter_slack_token_description
  ssm_parameter_gitlab_token_name        = var.ssm_parameter_gitlab_token_name == null ? "/${var.function_name}/gitlab-token" : var.ssm_parameter_gitlab_token_name
  ssm_parameter_gitlab_token_description = var.ssm_parameter_gitlab_token_description == null ? "GitLab token for Lambda function '${var.function_name}'." : var.ssm_parameter_gitlab_token_description
}

resource "null_resource" "this" {
  triggers = {
    shell_hash = sha256(file("${path.module}/files/requirements.txt"))
    runtime    = var.runtime
  }

  provisioner "local-exec" {
    command     = <<EOF
    rm -rf ${path.module}/files/packages/*
    mkdir -p ${path.module}/files/packages/python/lib/${var.runtime}/site-packages
    python3 -m pip install -r ${path.module}/files/requirements.txt -t ${path.module}/files/packages/python/lib/${var.runtime}/site-packages
  EOF
    interpreter = ["/bin/bash", "-c"]
  }
}

data "archive_file" "layer" {
  type        = "zip"
  source_dir  = "${path.module}/files/packages"
  output_path = "${path.module}/files/packages.zip"

  depends_on = [null_resource.this]
}

resource "aws_lambda_layer_version" "this" {
  layer_name               = coalesce(var.layer_name, var.function_name)
  description              = local.layer_description
  filename                 = data.archive_file.layer.output_path
  source_code_hash         = data.archive_file.layer.output_base64sha256
  compatible_runtimes      = [var.runtime]
  compatible_architectures = var.compatible_architectures
}

data "archive_file" "code" {
  type        = "zip"
  source_dir  = "${path.module}/files/code"
  output_path = "${path.module}/files/code.zip"
}

resource "aws_lambda_function" "this" {
  filename         = data.archive_file.code.output_path
  function_name    = var.function_name
  description      = var.description
  role             = aws_iam_role.this.arn
  handler          = "lambda.check_and_notify_stale_merge_requests"
  runtime          = var.runtime
  timeout          = var.timeout
  layers           = [aws_lambda_layer_version.this.arn]
  source_code_hash = data.archive_file.code.output_base64sha256
  publish          = var.publish

  reserved_concurrent_executions = var.reserved_concurrent_executions

  environment {
    variables = {
      EXCLUDE_GROUPS         = var.exclude_groups
      FALLBACK_CHANNEL_ID    = var.fallback_channel_id
      GITLAB_BASE_URL        = var.gitlab_base_url
      INTERNAL_EMAIL_DOMAINS = var.internal_email_domains
      PARAMETER_NAME_SLACK   = aws_ssm_parameter.slack_token.name
      PARAMETER_NAME_GITLAB  = aws_ssm_parameter.gitlab_token.name
      STALE_DAYS_THRESHOLD   = var.stale_days_threshold
    }
  }

  dynamic "tracing_config" {
    for_each = var.tracing_mode == null ? [] : [true]
    content {
      mode = var.tracing_mode
    }
  }

  tags = merge(var.tags, var.function_tags)

  depends_on = [aws_cloudwatch_log_group.lambda]
}

data "aws_iam_policy_document" "this" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "this" {
  name                = coalesce(var.role_name, var.function_name)
  description         = local.role_description
  assume_role_policy  = data.aws_iam_policy_document.this.json
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  inline_policy {
    name = "GetParameter"

    policy = jsonencode({
      Version : "2012-10-17",
      Statement : [
        {
          Action : "ssm:GetParameter",
          Effect : "Allow",
          Resource : [aws_ssm_parameter.slack_token.arn, aws_ssm_parameter.gitlab_token.arn]
        }
      ]
    })
  }
}

resource "aws_cloudwatch_event_rule" "this" {
  count = var.enable_scheduling ? 1 : 0

  name                = coalesce(var.cloudwatch_event_rule_name, var.function_name)
  description         = local.cloudwatch_event_rule_description
  schedule_expression = var.lambda_schedule
}

resource "aws_cloudwatch_event_target" "this" {
  count = var.enable_scheduling ? 1 : 0

  rule      = aws_cloudwatch_event_rule.this[0].name
  arn       = aws_lambda_function.this.arn
  target_id = var.function_name
}

resource "aws_lambda_permission" "this" {
  count = var.enable_scheduling ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this[0].arn
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.cloudwatch_logs_retention_in_days
  kms_key_id        = var.cloudwatch_logs_kms_key_id

  tags = merge(var.tags, var.cloudwatch_logs_tags)
}

resource "aws_ssm_parameter" "slack_token" {
  name        = local.ssm_parameter_slack_token_name
  description = local.ssm_parameter_slack_token_description
  type        = "SecureString"
  value       = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "gitlab_token" {
  name        = local.ssm_parameter_gitlab_token_name
  description = local.ssm_parameter_gitlab_token_description
  type        = "SecureString"
  value       = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}
