data "aws_route53_zone" "main" {
  name         = var.zone
  private_zone = false
}
