# AWS Lambda stale GitLab merge requests Slack app module

Terraform module which creates AWS Lambda function which notifies a Slack workspace about GitLab merge requests that haven't been updated within a certain amount of days. Messages the merge request author individually and posts a summary to the fallback channel. Posts to the fallback channel when the author of the merge request cannot be found.

The Lambda function uses values from the Parameter Store for API tokens. The value of these tokens needs to be updated manually, as this module will create them with the value `placeholder`.

## Install

You must have python3 and pip installed to generate `.zip` files for Lambda Function and layer.

## Usage

### Notify Slack users with 'example.com' email domain

```hcl
module "gitlab-stale-merge-requests-slack-app" {
  source = "github.com/alanjonesit/terraform-aws-gitlab-stale-merge-requests-slack-app"

  gitlab_base_url       = "https://gitlab.example.com"
  stale_days_threshold  = 7
  fallback_channel_id   = "#fallback-channel"
  internal_email_domains = ["example.com"]
  lambda_schedule       = "cron(0 1 ? * MON *)" # Monday 11am AEST
}
```

## GitLab and Slack permissions

### GitLab Token

The GitLab token will require the following permissions:

- [api](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#:~:text=Access-,api,-Grants%20complete%20read)

### Slack App

Your Slack app will require the following permissions:

- [chat:write](https://api.slack.com/scopes/chat:write)
- [im:write](https://api.slack.com/scopes/im:write)
- [users:read](https://api.slack.com/scopes/users:read)
- [users:read.email](https://api.slack.com/scopes/users:read.email)

The Slack app will also need to be added to the fallback channel.

## Slack message showcase

### Fallback channel message

```text
Total of 23 open merge requests not updated in the last 7 days, in non-archived projects.
Note: If the numbers below do not match the merge requests in GitLab, you may not have permission to view them.
- @User1 has a count of 4 # The number is a hyperlink to show the merge requests in GitLab
- @User2 has a count of 3
```

### Direct message

```text
You have open merge requests that haven't been updated in the last 7 days. Please review and take appropriate action.

Merge Request: feat: use components
Project: group-name/project-name
Last Updated: 15-03-2024 (37 days ago)
Status: :magnifying_glass_right: Approval is required before merge.
---
```

<!-- BEGIN_TF_DOCS -->

## Requirements

| Name                                                                     | Version |
| ------------------------------------------------------------------------ | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement_terraform) | >= 1.0  |
| <a name="requirement_archive"></a> [archive](#requirement_archive)       | >= 2.4  |
| <a name="requirement_aws"></a> [aws](#requirement_aws)                   | >= 5.0  |
| <a name="requirement_null"></a> [null](#requirement_null)                | >= 3.2  |

## Providers

| Name                                                         | Version |
| ------------------------------------------------------------ | ------- |
| <a name="provider_archive"></a> [archive](#provider_archive) | >= 2.4  |
| <a name="provider_aws"></a> [aws](#provider_aws)             | >= 5.0  |
| <a name="provider_null"></a> [null](#provider_null)          | >= 3.2  |

## Modules

No modules.

## Resources

| Name                                                                                                                                    | Type        |
| --------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| [aws_cloudwatch_event_rule.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule)     | resource    |
| [aws_cloudwatch_event_target.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource    |
| [aws_cloudwatch_log_group.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group)     | resource    |
| [aws_iam_role.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role)                               | resource    |
| [aws_lambda_function.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)                 | resource    |
| [aws_lambda_layer_version.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_layer_version)       | resource    |
| [aws_lambda_permission.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission)             | resource    |
| [aws_ssm_parameter.gitlab_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter)             | resource    |
| [aws_ssm_parameter.slack_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter)              | resource    |
| [null_resource.this](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource)                             | resource    |
| [archive_file.code](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file)                            | data source |
| [archive_file.layer](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file)                           | data source |
| [aws_iam_policy_document.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document)      | data source |

## Inputs

| Name                                                                                                                                                | Description                                                                                                                                                                                | Type           | Default                                   | Required |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- | ----------------------------------------- | :------: |
| <a name="input_cloudwatch_event_rule_description"></a> [cloudwatch_event_rule_description](#input_cloudwatch_event_rule_description)                | Description of CloudWatch event rule to use for Lambda Function.                                                                                                                           | `string`       | `null`                                    |    no    |
| <a name="input_cloudwatch_event_rule_name"></a> [cloudwatch_event_rule_name](#input_cloudwatch_event_rule_name)                                     | Name of CloudWatch event rule to use for Lambda Function.                                                                                                                                  | `string`       | `null`                                    |    no    |
| <a name="input_cloudwatch_logs_kms_key_id"></a> [cloudwatch_logs_kms_key_id](#input_cloudwatch_logs_kms_key_id)                                     | The ARN of the KMS Key to use when encrypting log data.                                                                                                                                    | `string`       | `null`                                    |    no    |
| <a name="input_cloudwatch_logs_retention_in_days"></a> [cloudwatch_logs_retention_in_days](#input_cloudwatch_logs_retention_in_days)                | Specifies the number of days you want to retain log events in the specified log group. Possible values are: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, and 3653. | `number`       | `365`                                     |    no    |
| <a name="input_cloudwatch_logs_tags"></a> [cloudwatch_logs_tags](#input_cloudwatch_logs_tags)                                                       | A map of tags to assign to the resource.                                                                                                                                                   | `map(string)`  | `{}`                                      |    no    |
| <a name="input_compatible_architectures"></a> [compatible_architectures](#input_compatible_architectures)                                           | A list of Architectures Lambda layer is compatible with. Currently x86_64 and arm64 can be specified.                                                                                      | `list(string)` | `null`                                    |    no    |
| <a name="input_enable_scheduling"></a> [enable_scheduling](#input_enable_scheduling)                                                                | Enable scheduling so that Lambda automatically triggers based on cron expression.                                                                                                          | `bool`         | `true`                                    |    no    |
| <a name="input_exclude_groups"></a> [exclude_groups](#input_exclude_groups)                                                                         | Define keywords to filter out GitLab Groups from the function. Example 'group1, group2'.                                                                                                   | `string`       | `""`                                      |    no    |
| <a name="input_fallback_channel_id"></a> [fallback_channel_id](#input_fallback_channel_id)                                                          | ID of the fallback channel for notifications. Can use the format '#channel-name'.                                                                                                          | `string`       | n/a                                       |   yes    |
| <a name="input_function_description"></a> [function_description](#input_function_description)                                                       | Description of the Lambda Function                                                                                                                                                         | `string`       | `null`                                    |    no    |
| <a name="input_function_name"></a> [function_name](#input_function_name)                                                                            | A unique name for the Lambda Function                                                                                                                                                      | `string`       | `"gitlab-stale-merge-requests-slack-app"` |    no    |
| <a name="input_gitlab_base_url"></a> [gitlab_base_url](#input_gitlab_base_url)                                                                      | Base URL for the GitLab API including 'https://'.                                                                                                                                          | `string`       | n/a                                       |   yes    |
| <a name="input_internal_email_domains"></a> [internal_email_domains](#input_internal_email_domains)                                                 | List of internal email domains for GitLab users. Used to message only internal users. Example 'domain1.com, domain2.com'.                                                                  | `string`       | `null`                                    |    no    |
| <a name="input_lambda_schedule"></a> [lambda_schedule](#input_lambda_schedule)                                                                      | When to trigger Lambda function. Set value in cron format.                                                                                                                                 | `string`       | `null`                                    |    no    |
| <a name="input_layer_description"></a> [layer_description](#input_layer_description)                                                                | Description of Lambda layer to use for Lambda Function.                                                                                                                                    | `string`       | `null`                                    |    no    |
| <a name="input_layer_name"></a> [layer_name](#input_layer_name)                                                                                     | Name of Lambda layer to use for Lambda Function.                                                                                                                                           | `string`       | `null`                                    |    no    |
| <a name="input_publish"></a> [publish](#input_publish)                                                                                              | Whether to publish creation/change as new Lambda Function Version.                                                                                                                         | `bool`         | `false`                                   |    no    |
| <a name="input_reserved_concurrent_executions"></a> [reserved_concurrent_executions](#input_reserved_concurrent_executions)                         | The amount of reserved concurrent executions for the Lambda Function. A value of 0 disables Lambda Function from being triggered and -1 removes any concurrency limitations.               | `number`       | `1`                                       |    no    |
| <a name="input_role_description"></a> [role_description](#input_role_description)                                                                   | Description of IAM role to use for Lambda Function.                                                                                                                                        | `string`       | `null`                                    |    no    |
| <a name="input_role_name"></a> [role_name](#input_role_name)                                                                                        | Name of IAM role to use for Lambda Function.                                                                                                                                               | `string`       | `null`                                    |    no    |
| <a name="input_runtime"></a> [runtime](#input_runtime)                                                                                              | Lambda Function runtime                                                                                                                                                                    | `string`       | `"python3.12"`                            |    no    |
| <a name="input_ssm_parameter_gitlab_token_description"></a> [ssm_parameter_gitlab_token_description](#input_ssm_parameter_gitlab_token_description) | Description of SSM parameter for GitLab token.                                                                                                                                             | `string`       | `null`                                    |    no    |
| <a name="input_ssm_parameter_gitlab_token_name"></a> [ssm_parameter_gitlab_token_name](#input_ssm_parameter_gitlab_token_name)                      | Name of SSM parameter for GitLab token.                                                                                                                                                    | `string`       | `null`                                    |    no    |
| <a name="input_ssm_parameter_slack_token_description"></a> [ssm_parameter_slack_token_description](#input_ssm_parameter_slack_token_description)    | Description of SSM parameter for Slack token.                                                                                                                                              | `string`       | `null`                                    |    no    |
| <a name="input_ssm_parameter_slack_token_name"></a> [ssm_parameter_slack_token_name](#input_ssm_parameter_slack_token_name)                         | Name of SSM parameter for Slack token.                                                                                                                                                     | `string`       | `null`                                    |    no    |
| <a name="input_stale_days_threshold"></a> [stale_days_threshold](#input_stale_days_threshold)                                                       | Threshold in days for considering a merge request as stale.                                                                                                                                | `number`       | `7`                                       |    no    |
| <a name="input_timeout"></a> [timeout](#input_timeout)                                                                                              | The amount of time the Lambda Function has to run in seconds.                                                                                                                              | `number`       | `120`                                     |    no    |
| <a name="input_tracing_mode"></a> [tracing_mode](#input_tracing_mode)                                                                               | Tracing mode of the Lambda Function. Valid value can be either PassThrough or Active.                                                                                                      | `string`       | `null`                                    |    no    |

## Outputs

| Name                                                                                                                             | Description                                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| <a name="output_cloudwatch_event_rule_name"></a> [cloudwatch_event_rule_name](#output_cloudwatch_event_rule_name)                | The name of the CloudWatch Event Rule. Returns 'Scheduling not enabled' if scheduling is disabled. |
| <a name="output_cloudwatch_log_group_name"></a> [cloudwatch_log_group_name](#output_cloudwatch_log_group_name)                   | The name of the CloudWatch Log Group associated with the Lambda function.                          |
| <a name="output_code_zip_path"></a> [code_zip_path](#output_code_zip_path)                                                       | The path to the zipped code for the Lambda function.                                               |
| <a name="output_iam_role_arn"></a> [iam_role_arn](#output_iam_role_arn)                                                          | The ARN of the IAM role used by the Lambda function.                                               |
| <a name="output_lambda_function_arn"></a> [lambda_function_arn](#output_lambda_function_arn)                                     | The ARN of the Lambda function.                                                                    |
| <a name="output_lambda_function_name"></a> [lambda_function_name](#output_lambda_function_name)                                  | The name of the Lambda function.                                                                   |
| <a name="output_lambda_layer_version_arn"></a> [lambda_layer_version_arn](#output_lambda_layer_version_arn)                      | The ARN of the Lambda layer version.                                                               |
| <a name="output_layer_zip_path"></a> [layer_zip_path](#output_layer_zip_path)                                                    | The path to the zipped Lambda layer package.                                                       |
| <a name="output_ssm_parameter_gitlab_token_name"></a> [ssm_parameter_gitlab_token_name](#output_ssm_parameter_gitlab_token_name) | The name of the SSM parameter that stores the GitLab token.                                        |
| <a name="output_ssm_parameter_slack_token_name"></a> [ssm_parameter_slack_token_name](#output_ssm_parameter_slack_token_name)    | The name of the SSM parameter that stores the Slack token.                                         |

<!-- END_TF_DOCS -->

## Authors

- [Alan Jones](https://github.com/alanjonesit)

## Contributing

All contributions are welcome.

## Licence

GPL-3.0 licensed. See license in [LICENSE](/LICENSE).
