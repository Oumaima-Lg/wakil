# PostgreSQL Flexible Server : un seul serveur (le plus petit, gratuit 12 mois pour un nouveau compte), trois bases,
# comme en local : la banque, les conversations de l'agent, les vecteurs de la FAQ.
#
# Les rôles de chaque service (avec leurs mots de passe de Key Vault), les tables et les données fictives sont créés
# au premier déploiement par un job d'initialisation, qui rejoue les scripts du dépôt (schema.sql, base-agent.sh,
# base-faq.sh, le script des fausses données, l'indexation de la FAQ) : Terraform ne gère que le serveur.
#
# Piège à connaître : un serveur arrêté redémarre tout seul au bout de 7 jours (limite d'Azure).

locals {
  bases = {
    banque = "banque_atlas_demo"
    agent  = "wakil_agent"
    faq    = "wakil_faq"
  }
}

# Joignable par Internet, réservé aux services Azure (règle de pare-feu 0.0.0.0) et protégé par mot de passe et TLS :
# Container Apps en plan consommation n'a pas d'adresse fixe, et un réseau privé sort du budget.
#trivy:ignore:AZU-0022
resource "azurerm_postgresql_flexible_server" "base" {
  name                              = "psql-${local.nom}-${random_string.suffixe.result}"
  resource_group_name               = azurerm_resource_group.demo.name
  location                          = azurerm_resource_group.demo.location
  version                           = "17"
  sku_name                          = "B_Standard_B1ms"
  storage_mb                        = 32768
  backup_retention_days             = 7
  geo_redundant_backup_enabled      = false
  public_network_access_enabled     = true
  administrator_login               = "wakiladmin"
  administrator_password_wo         = ephemeral.random_password.postgres["admin"].result # jamais dans l'état
  administrator_password_wo_version = var.version_des_secrets
  zone                              = "1"
  tags                              = local.etiquettes

  authentication {
    password_auth_enabled         = true
    active_directory_auth_enabled = false
  }
}

# pgvector doit être autorisé avant « CREATE EXTENSION vector » (base de la FAQ).
resource "azurerm_postgresql_flexible_server_configuration" "extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.base.id
  value     = "VECTOR"
}

resource "azurerm_postgresql_flexible_server_database" "bases" {
  for_each  = local.bases
  name      = each.value
  server_id = azurerm_postgresql_flexible_server.base.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Chaque connexion et chaque point de reprise sont journalisés, et les échecs de connexion répétés sont freinés (essais de mots de passe).
resource "azurerm_postgresql_flexible_server_configuration" "parametres" {
  for_each = {
    "log_checkpoints"            = "on"
    "log_connections"            = "on"
    "log_disconnections"         = "on"
    "connection_throttle.enable" = "on"
  }
  name      = each.key
  server_id = azurerm_postgresql_flexible_server.base.id
  value     = each.value
}

# « Allow access to Azure services » : 0.0.0.0, la convention d'Azure pour ses propres services.
resource "azurerm_postgresql_flexible_server_firewall_rule" "services_azure" {
  name             = "services-azure"
  server_id        = azurerm_postgresql_flexible_server.base.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
