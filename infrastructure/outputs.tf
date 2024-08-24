output "resource_group" {
  value = azurerm_resource_group.main.name
}
output "name" {
  value = var.name
}
output "function" {
  value = azurerm_linux_function_app.main.name
}
