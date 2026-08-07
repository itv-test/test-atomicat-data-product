locals {
  unit        = basename(get_original_terragrunt_dir())
  environment = basename(dirname(get_original_terragrunt_dir()))
  project_id  = "itv-data-${local.common_vars.domain}-dom-${local.environment}"
  common_vars = read_terragrunt_config(find_in_parent_folders("common.hcl")).locals
  root_vars = {
    environment                  = local.environment
    project_id                   = local.project_id
    terraform_service_account    = "tf-${local.common_vars.data_product_name}@itv-data-envconfig-${local.environment}.iam.gserviceaccount.com"
    data_product_service_account = "ex-${local.common_vars.data_product_name}@${local.project_id}.iam.gserviceaccount.com"
  }
}

terraform {
  source = "${path_relative_from_include()}/terraform/${local.unit}"
}

inputs = merge(
  local.common_vars,
  local.root_vars,
)

remote_state {
  backend = "gcs"
  config = {
    skip_bucket_creation        = true
    bucket                      = "itv-data-platform-tf-data-products-${local.environment}"
    prefix                      = "${local.common_vars.domain}/${local.common_vars.data_product_name}/${local.unit}"
    project                     = "itv-data-envconfig-${local.environment}"
    location                    = local.common_vars.region
    enable_bucket_policy_only   = true
    impersonate_service_account = "${local.root_vars.terraform_service_account}"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
terraform {
  backend "gcs" {}
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "~>7.0"
    }
  }
}
provider "google" {
  default_labels = {
      deployment_tool = "terraform",
      managed_by      = "platform"
  }
  impersonate_service_account = "${local.root_vars.terraform_service_account}"
}
EOF
}
