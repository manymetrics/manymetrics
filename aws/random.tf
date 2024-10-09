resource "random_string" "unique_key" {
  length  = 8
  special = false
  upper   = false
}
