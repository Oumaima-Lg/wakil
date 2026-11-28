# Les secrets de Wakil, rangés dans Key Vault, et jamais dans l'état Terraform.
#
# Le piège classique de Terraform : un mot de passe généré par une ressource (random_password) est écrit en clair dans
# le fichier d'état. Ici, il est généré par une ressource « éphémère », qui n'existe que pendant le passage de Terraform,
# et transmis à Azure par des arguments en « écriture seule » (value_wo, administrator_password_wo), qu'Azure reçoit et
# que Terraform n'enregistre jamais. Pour les faire tourner : augmenter var.version_des_secrets.
#
# Chaque service ne pourra lire que ses propres secrets (rôle Key Vault Secrets User sur chaque secret, pas sur le coffre
# entier, voir applications.tf) : la clé privée des sessions pour portail-api seulement, celle des jetons courts pour
# mcp-tools seulement.

# Container Apps sans réseau privé (hors budget) : le coffre reste joignable par Internet, protégé par Entra ID et RBAC.
# La protection contre la purge est coupée : la démo est détruite et recréée souvent, avec le même nom de coffre ; la
# suppression douce (7 jours) reste active.
#trivy:ignore:AZU-0013
#trivy:ignore:AZU-0016
resource "azurerm_key_vault" "secrets" {
  name                       = "kv-wakil-${random_string.suffixe.result}"
  resource_group_name        = azurerm_resource_group.demo.name
  location                   = azurerm_resource_group.demo.location
  tenant_id                  = data.azurerm_client_config.actuel.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true # des rôles Azure, pas de « politiques d'accès » propres au coffre
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  tags                       = local.etiquettes
}

# Qui lance Terraform écrit les secrets dans le coffre.
resource "azurerm_role_assignment" "terraform_ecrit_les_secrets" {
  scope                = azurerm_key_vault.secrets.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.actuel.object_id
}

# --- Générés le temps d'un passage, jamais enregistrés --------------------------------------------------------------

ephemeral "random_password" "postgres" {
  for_each = toset(["admin", "banque", "agent", "faq"])
  length   = 32
  special  = false # pas de caractère à échapper dans une chaîne de connexion
}

# Les deux paires de clés RS256 : les sessions (portail-api signe, les autres vérifient) et les jetons courts vers la
# banque (mcp-tools signe, bank-api vérifie). ADR 0004.
ephemeral "tls_private_key" "jetons" {
  for_each  = toset(["session", "mcp"])
  algorithm = "RSA"
  rsa_bits  = 2048
}

locals {
  # Les services attendent une clé sur une ligne : le binaire DER en base64 (voir apps/portail-api/app/cles.py). Le
  # corps d'un fichier PEM est exactement ce base64 : on retire l'en-tête, le pied et les retours à la ligne.
  der_base64 = {
    for nom, cle in ephemeral.tls_private_key.jetons : nom => {
      privee   = replace(replace(replace(cle.private_key_pem_pkcs8, "-----BEGIN PRIVATE KEY-----", ""), "-----END PRIVATE KEY-----", ""), "\n", "")
      publique = replace(replace(replace(cle.public_key_pem, "-----BEGIN PUBLIC KEY-----", ""), "-----END PUBLIC KEY-----", ""), "\n", "")
    }
  }

  # Le nom de chaque secret dans le coffre, et sa valeur (éphémère).
  secrets = {
    "postgres-admin-mdp"   = ephemeral.random_password.postgres["admin"].result
    "postgres-banque-mdp"  = ephemeral.random_password.postgres["banque"].result
    "postgres-agent-mdp"   = ephemeral.random_password.postgres["agent"].result
    "postgres-faq-mdp"     = ephemeral.random_password.postgres["faq"].result
    "session-cle-privee"   = local.der_base64["session"].privee
    "session-cle-publique" = local.der_base64["session"].publique
    "mcp-cle-privee"       = local.der_base64["mcp"].privee
    "mcp-cle-publique"     = local.der_base64["mcp"].publique
  }
}

# Pas de date d'expiration : un secret expiré couperait la démo sans prévenir. Ils tournent par var.version_des_secrets.
#trivy:ignore:AZU-0017
resource "azurerm_key_vault_secret" "secrets" {
  for_each         = toset(keys(local.secrets)) # les noms seulement : les valeurs éphémères ne servent pas de clés
  name             = each.key
  key_vault_id     = azurerm_key_vault.secrets.id
  value_wo         = local.secrets[each.key]
  value_wo_version = var.version_des_secrets
  content_type     = "text/plain"
  tags             = local.etiquettes

  depends_on = [azurerm_role_assignment.terraform_ecrit_les_secrets]
}
