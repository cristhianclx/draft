resource "azurerm_storage_container" "files" {
  name                  = "files"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "blob"
}
resource "azurerm_storage_container" "screens" {
  name                  = "screens"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "blob"
}
