resource "aws_ecr_repository" "event_spark" {
  name = "manymetrics-spark-${var.name}"

  force_delete = true
}

resource "aws_ecr_lifecycle_policy" "event_spark" {
  repository = aws_ecr_repository.event_spark.name

  policy = jsonencode({
    "rules" : [
      {
        "rulePriority" : 1,
        "description" : "Keep last 10 images",
        "selection" : {
          "tagStatus" : "any",
          "countType" : "imageCountMoreThan",
          "countNumber" : 10
        },
        "action" : {
          "type" : "expire"
        }
      }
    ]
  })
}
