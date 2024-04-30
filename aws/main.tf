data "aws_region" "current" {}

resource "random_string" "random" {
  length  = 8
  special = false
  upper   = false
}
