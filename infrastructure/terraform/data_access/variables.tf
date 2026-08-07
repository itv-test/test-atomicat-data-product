variable "project_id" {
  type = string
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "pre", "prd"], var.environment)
    error_message = "The environment must be one of 'dev', 'pre' or 'prd'."
  }
}

variable "product_table_access" {
  type        = map(map(list(string)))
  default     = {}
  description = <<-EOT
  A map of table names to lists of readers who should have access to them. Example:
  {
    table_name1 = {
      readers = ["serviceAccount:myserviceaccount@myproject.com"]
    }
    ...
  }
  EOT
}
