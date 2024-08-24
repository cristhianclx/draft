resource "aws_route53_record" "function_validation" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "asuid.${var.name}"
  type    = "TXT"
  ttl     = 300
  records = [
    azurerm_linux_function_app.main.custom_domain_verification_id,
  ]
}

resource "aws_route53_record" "function" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.name
  type    = "CNAME"
  ttl     = 300
  records = [
    azurerm_linux_function_app.main.default_hostname,
  ]
}

resource "azurerm_app_service_custom_hostname_binding" "main" {
  hostname            = var.name
  app_service_name    = azurerm_linux_function_app.main.name
  resource_group_name = azurerm_resource_group.main.name
  depends_on = [
    aws_route53_record.function_validation,
    aws_route53_record.function,
  ]
}
