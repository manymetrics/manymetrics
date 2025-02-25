resource "aws_ecr_repository" "loader" {
  name = "manymetrics-loader-${var.name}"

  force_delete = true
}

resource "aws_ecr_lifecycle_policy" "loader" {
  repository = aws_ecr_repository.loader.name

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
