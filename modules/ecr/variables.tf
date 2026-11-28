variable "name_prefix" {
  type = string
}

variable "repository_names" {
  type    = list(string)
  default = ["api", "worker"]
}

variable "force_delete" {
  type    = bool
  default = false
}

variable "keep_last_images" {
  type    = number
  default = 5
}