resource "random_password" "database_credentials_password" {
  length           = 16
  special          = true
  override_special = "_%@"
}

resource "tidbcloud_cluster" "main" {
  project_id     = var.tidb_project_id
  name           = replace(var.name, ".", "-")
  cluster_type   = "DEVELOPER"
  cloud_provider = "AWS"
  region         = "us-east-1"
  config = {
    root_password = random_password.database_credentials_password.result
  }
}
