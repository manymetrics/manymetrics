variable "name" {
    description = "A name to identify the resources created by this module"
    type        = string
    # allowed only alphanumeric characters and hyphens
    validation {
        condition     = can(regex("^[a-zA-Z0-9-]+$", var.name))
        error_message = "The unique key must contain only alphanumeric characters and hyphens"
    }
}
