resource "azurerm_resource_group" "main" {
  name     = var.name
  location = "East US"
}

resource "azurerm_storage_account" "main" {
  name                     = replace(replace("storage-${var.name}", ".", ""), "-", "")
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "main" {
  name                = replace(var.name, ".", "-")
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "main" {
  name                       = replace("function-${var.name}", ".", "-")
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  service_plan_id            = azurerm_service_plan.main.id
  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key
  https_only                 = true

  site_config {
    application_stack {
      python_version = 3.11
    }
  }
  app_settings = {
    "AzureWebJobsDashboard"          = azurerm_storage_account.main.primary_connection_string
    "AzureWebJobsFeatureFlags"       = "EnableWorkerIndexing"
    "AzureWebJobsStorage"            = azurerm_storage_account.main.primary_connection_string
    "DATABASE_HOST"                  = tidbcloud_cluster.main.status.connection_strings.standard.host
    "DATABASE_PORT"                  = tidbcloud_cluster.main.status.connection_strings.standard.port
    "DATABASE_NAME"                  = "test"
    "DATABASE_USER"                  = tidbcloud_cluster.main.status.connection_strings.default_user
    "DATABASE_PASSWORD"              = tidbcloud_cluster.main.config.root_password
    "FUNCTIONS_WORKER_RUNTIME"       = "python"
    "OPENAI_API_KEY"                 = "-"
    "STORAGE_CONTAINER_FILES_NAME"   = azurerm_storage_container.files.name
    "STORAGE_CONTAINER_SCREENS_NAME" = azurerm_storage_container.screens.name
  }
  lifecycle {
    ignore_changes = [
      app_settings["AzureWebJobsDashboard"],
      app_settings["AzureWebJobsStorage"],
      app_settings["OPENAI_API_KEY"]
    ]
  }
}
