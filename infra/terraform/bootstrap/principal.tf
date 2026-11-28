# Le « bootstrap » : ce qui doit exister avant l'environnement de la démo, et lui survivre quand on le détruit.
#
# 1. Le stockage de l'état Terraform de l'environnement (sa mémoire de ce qu'il a créé) : un compte de stockage sans
#    clé partagée, accessible seulement avec une identité Entra ID, avec l'historique des versions de l'état.
# 2. L'alerte de budget de l'abonnement : un courriel à 50 %, 80 % et 100 % du budget dépensé, et quand la prévision du
#    mois dépasse le budget. Une alerte prévient, elle ne coupe rien : « terraform destroy » reste le vrai frein.
#
# Son propre état reste local (dans ce dossier, jamais commité) : il ne contient aucun secret, et ce module ne change
# presque jamais. L'abonnement vient de la variable d'environnement ARM_SUBSCRIPTION_ID, jamais d'un fichier.

provider "azurerm" {
  features {}
  storage_use_azuread = true # le stockage se gère par Entra ID : les clés partagées sont désactivées plus bas
}

data "azurerm_client_config" "actuel" {}
data "azurerm_subscription" "actuelle" {}

locals {
  etiquettes = {
    projet = "wakil"
    env    = "etat"
    owner  = var.proprietaire
    ttl    = "permanent" # survit aux « terraform destroy » de la démo
  }
}

resource "random_string" "suffixe" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_resource_group" "etat" {
  name     = "rg-wakil-etat"
  location = var.region
  tags     = local.etiquettes
}

# Le réseau public reste ouvert : l'état est lu depuis le PC et depuis GitHub Actions, sans réseau privé (hors budget).
# Seules les identités Entra ID autorisées y accèdent : aucune clé partagée, aucun accès anonyme. Écarts assumés pour
# une démo : clés de chiffrement gérées par Microsoft (avec un second chiffrement de l'infrastructure), une seule
# région (LRS), pas de journaux de stockage classiques (ils demandent les clés partagées, désactivées ici).
#trivy:ignore:AZU-0012
#trivy:ignore:AZU-0057
#trivy:ignore:AZU-0058
#trivy:ignore:AZU-0060
resource "azurerm_storage_account" "etat" {
  name                              = "stwakiletat${random_string.suffixe.result}"
  resource_group_name               = azurerm_resource_group.etat.name
  location                          = azurerm_resource_group.etat.location
  account_tier                      = "Standard"
  account_replication_type          = "LRS"
  min_tls_version                   = "TLS1_2"
  https_traffic_only_enabled        = true
  shared_access_key_enabled         = false
  default_to_oauth_authentication   = true
  allow_nested_items_to_be_public   = false
  infrastructure_encryption_enabled = true

  blob_properties {
    versioning_enabled = true # chaque écriture de l'état garde la version d'avant : une erreur se rattrape

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }
  }

  tags = local.etiquettes
}

resource "azurerm_storage_container" "etat" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.etat.id
  container_access_type = "private"
}

# Qui lance Terraform (toi, puis le pipeline) doit pouvoir lire et écrire l'état, sans clé partagée.
resource "azurerm_role_assignment" "etat" {
  scope                = azurerm_storage_account.etat.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.actuel.object_id
}

resource "azurerm_consumption_budget_subscription" "mensuel" {
  name            = "budget-wakil"
  subscription_id = data.azurerm_subscription.actuelle.id
  amount          = var.budget_mensuel
  time_grain      = "Monthly"

  time_period {
    start_date = formatdate("YYYY-MM-01'T'00:00:00Z", timestamp()) # le premier jour du mois de création
  }

  dynamic "notification" {
    for_each = toset([50, 80, 100])
    content {
      operator       = "GreaterThanOrEqualTo"
      threshold      = notification.value
      threshold_type = "Actual"
      contact_emails = var.courriels_alertes
    }
  }

  notification {
    operator       = "GreaterThanOrEqualTo"
    threshold      = 100
    threshold_type = "Forecasted"
    contact_emails = var.courriels_alertes
  }

  lifecycle {
    ignore_changes = [time_period] # timestamp() change à chaque plan : la date de départ ne bouge plus après la création
  }
}
