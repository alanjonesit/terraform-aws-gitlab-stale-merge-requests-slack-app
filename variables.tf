###############
# Function code
###############

variable "gitlab_base_url" {
  description = "Base URL for the GitLab API including 'https://'."
  type        = string
  default     = "https://gitlab.com"
}

variable "stale_days_threshold" {
  description = "Threshold in days for considering a merge request as stale."
  type        = number
  default     = 7
}

variable "fallback_channel_id" {
  description = "ID of the fallback channel for notifications. Can use the format '#channel-name'."
  type        = string
}

variable "internal_email_domains" {
  description = "List of internal email domains for GitLab users. Used to message only internal users.  Example 'domain1.com, domain2.com'."
  type        = string
  default     = null
}

variable "exclude_groups" {
  description = "Define keywords to filter out GitLab Groups from the function. Example 'group1, group2'."
  type        = string
  default     = ""
}

###########
# Function
###########

variable "function_name" {
  description = "A unique name for the Lambda Function"
  type        = string
  default     = "gitlab-stale-merge-requests-slack-app"
}

variable "runtime" {
  description = "Lambda Function runtime"
  type        = string
  default     = "python3.12"
}

variable "function_description" {
  description = "Description of the Lambda Function"
  type        = string
  default     = null
}

variable "publish" {
  description = "Whether to publish creation/change as new Lambda Function Version."
  type        = bool
  default     = false
}

variable "reserved_concurrent_executions" {
  description = "The amount of reserved concurrent executions for the Lambda Function. A value of 0 disables Lambda Function from being triggered and -1 removes any concurrency limitations."
  type        = number
  default     = 1
}

variable "timeout" {
  description = "The amount of time the Lambda Function has to run in seconds."
  type        = number
  default     = 120
}

variable "tracing_mode" {
  description = "Tracing mode of the Lambda Function. Valid value can be either PassThrough or Active."
  type        = string
  default     = null
}

########
# Layer
########

variable "layer_name" {
  description = "Name of Lambda layer to use for Lambda Function."
  type        = string
  default     = null
}

variable "layer_description" {
  description = "Description of Lambda layer to use for Lambda Function."
  type        = string
  default     = null
}

variable "compatible_architectures" {
  description = "A list of Architectures Lambda layer is compatible with. Currently x86_64 and arm64 can be specified."
  type        = list(string)
  default     = null
}

#######################
# CloudWatch Event Rule
#######################

variable "enable_scheduling" {
  description = "Enable scheduling so that Lambda automatically triggers based on cron expression."
  type        = bool
  default     = true
}

variable "lambda_schedule" {
  description = "When to trigger Lambda function. Set value in cron format."
  type        = string
  default     = null
}

variable "cloudwatch_event_rule_name" {
  description = "Name of CloudWatch event rule to use for Lambda Function."
  type        = string
  default     = null
}

variable "cloudwatch_event_rule_description" {
  description = "Description of CloudWatch event rule to use for Lambda Function."
  type        = string
  default     = null
}

#################
# CloudWatch Logs
#################

variable "cloudwatch_logs_retention_in_days" {
  description = "Specifies the number of days you want to retain log events in the specified log group. Possible values are: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, and 3653."
  type        = number
  default     = 365
}

variable "cloudwatch_logs_kms_key_id" {
  description = "The ARN of the KMS Key to use when encrypting log data."
  type        = string
  default     = null
}

variable "cloudwatch_logs_tags" {
  description = "A map of tags to assign to the resource."
  type        = map(string)
  default     = {}
}

###############
# SSM Parameter
###############

variable "ssm_parameter_slack_token_name" {
  description = "Name of SSM parameter for Slack token."
  type        = string
  default     = null
}

variable "ssm_parameter_slack_token_description" {
  description = "Description of SSM parameter for Slack token."
  type        = string
  default     = null
}

variable "ssm_parameter_gitlab_token_name" {
  description = "Name of SSM parameter for GitLab token."
  type        = string
  default     = null
}

variable "ssm_parameter_gitlab_token_description" {
  description = "Description of SSM parameter for GitLab token."
  type        = string
  default     = null
}

##########
# IAM Role
##########

variable "role_name" {
  description = "Name of IAM role to use for Lambda Function."
  type        = string
  default     = null
}

variable "role_description" {
  description = "Description of IAM role to use for Lambda Function."
  type        = string
  default     = null
}
