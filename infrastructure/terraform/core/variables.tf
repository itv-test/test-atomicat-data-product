variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "domain" {
  type = string
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "pre", "prd"], var.environment)
    error_message = "The environment must be one of 'dev', 'pre' or 'prd'."
  }
}

variable "data_product_name" {
  type = string
}

variable "data_product_owner_email_address" {
  type = string
}

variable "data_custodian_email_address" {
  type = string
}

variable "publish_to_catalogue" {
  type = bool
}
