terraform {
  required_version = "~> 1.17.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.13.0" # publiée depuis plus de deux semaines (règle des dépendances du projet)
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.9.1"
    }
  }
}
