variable "region" {
  description = "La région Azure (la plus proche du Maroc qui propose Container Apps et PostgreSQL Flexible)."
  type        = string
  default     = "francecentral"
}

variable "environnement" {
  description = "Le nom de l'environnement, dans les noms et l'étiquette « env »."
  type        = string
  default     = "demo"

  validation {
    condition     = can(regex("^[a-z0-9]{2,8}$", var.environnement))
    error_message = "De 2 à 8 lettres minuscules ou chiffres (il entre dans des noms Azure courts)."
  }
}

variable "proprietaire" {
  description = "L'étiquette « owner » : qui répond de ces ressources."
  type        = string
}

variable "duree_de_vie" {
  description = "L'étiquette « ttl » : jusqu'à quand l'environnement peut vivre avant un « terraform destroy »."
  type        = string
  default     = "detruire-apres-la-demo"
}

variable "version_images" {
  description = "L'étiquette des images à déployer (le SHA du commit, posé par le pipeline)."
  type        = string
}

variable "modele" {
  description = "Le LLM de Wakil, servi par le conteneur Ollama (ADR 0003)."
  type        = string
  default     = "qwen3:4b-instruct"
}

variable "version_des_secrets" {
  description = <<-EOT
    Les mots de passe et les clés sont générés à chaque passage, mais Azure ne les reçoit qu'à la création ou quand ce
    nombre change : l'augmenter fait tourner tous les secrets d'un coup (puis relancer le job d'initialisation).
  EOT
  type        = number
  default     = 1
}

variable "journaux_go_par_jour" {
  description = "Le plafond journalier de Log Analytics, en Go."
  type        = number
  default     = 0.1
}
