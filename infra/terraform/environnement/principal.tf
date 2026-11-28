# L'environnement de la démo Wakil sur Azure : tout ce que « terraform destroy » supprime quand la démo ne sert pas.
#
#   registre.tf      les images (Azure Container Registry)
#   secrets.tf       Key Vault, et les secrets générés sans jamais passer par l'état Terraform
#   base.tf          PostgreSQL Flexible Server (pgvector) et ses trois bases
#   applications.tf  les identités, l'environnement Container Apps et les sept conteneurs
#
# Données 100 % fictives. L'abonnement vient de ARM_SUBSCRIPTION_ID ; l'état est rangé dans le compte de stockage créé
# par le bootstrap (init : terraform init -backend-config=etat.tfbackend, voir docs/developpement.md).

provider "azurerm" {
  features {}
  storage_use_azuread = true
}

terraform {
  backend "azurerm" {
    key              = "environnement.tfstate"
    use_azuread_auth = true # aucune clé de stockage : l'identité de qui lance Terraform
  }
}

data "azurerm_client_config" "actuel" {}

locals {
  etiquettes = {
    projet = "wakil"
    env    = var.environnement
    owner  = var.proprietaire
    ttl    = var.duree_de_vie
  }
  nom = "wakil-${var.environnement}"
}

resource "random_string" "suffixe" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_resource_group" "demo" {
  name     = "rg-${local.nom}"
  location = var.region
  tags     = local.etiquettes
}

resource "azurerm_log_analytics_workspace" "journaux" {
  name                = "log-${local.nom}"
  resource_group_name = azurerm_resource_group.demo.name
  location            = azurerm_resource_group.demo.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = var.journaux_go_par_jour # plafond : au-delà, les journaux du jour sont perdus, pas facturés
  tags                = local.etiquettes
}
