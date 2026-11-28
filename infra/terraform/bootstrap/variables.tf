variable "region" {
  description = "La région Azure, la même que celle de l'environnement."
  type        = string
  default     = "francecentral"
}

variable "proprietaire" {
  description = "L'étiquette « owner » : qui répond de ces ressources."
  type        = string
}

variable "budget_mensuel" {
  description = "Le budget mensuel de l'abonnement, en USD."
  type        = number
  default     = 10

  validation {
    condition     = var.budget_mensuel > 0
    error_message = "Le budget doit être positif."
  }
}

variable "courriels_alertes" {
  description = "Les adresses qui reçoivent les alertes de budget (dans terraform.tfvars, jamais commité)."
  type        = list(string)

  validation {
    condition     = length(var.courriels_alertes) > 0
    error_message = "Il faut au moins une adresse pour les alertes de budget."
  }
}
