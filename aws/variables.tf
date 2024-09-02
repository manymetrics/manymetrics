# variable "unique_key" {
#     description = "A unique key to identify the resources created by this module"
#     type        = string
#     # allowed only alphanumeric characters and hyphens
#     validation {
#         condition     = can(regex("^[a-zA-Z0-9-]+$", var.unique_key))
#         error_message = "The unique key must contain only alphanumeric characters and hyphens"
#     }
# }
