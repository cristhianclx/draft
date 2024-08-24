terraform {
  required_version = ">=1.9.4"

  backend "s3" {
    bucket               = "infrastructure.demo.pe"
    key                  = "draft.demo.pe"
    encrypt              = "true"
    region               = "sa-east-1"
    workspace_key_prefix = "tf"
  }
}
