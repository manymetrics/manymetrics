resource "aws_glue_catalog_database" "database" {
  name = "manymetrics_${var.name}"
}
