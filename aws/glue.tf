resource "aws_glue_catalog_database" "database" {
  name = "manymetrics_${random_string.random.result}"
}
