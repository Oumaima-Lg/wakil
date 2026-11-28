# Les sept conteneurs de Wakil dans Azure Container Apps (l'équivalent d'ECS Fargate ou App Runner) : les six services
# du dépôt et Ollama. Seul le site est public, en HTTPS ; les autres ne se joignent qu'à l'intérieur de l'environnement,
# par leur nom (http://bank-api, http://mcp-tools/mcp…), comme dans docker-compose.yml (profil « images »).
#
# Chaque service a sa propre identité, avec le minimum de droits : tirer ses images (AcrPull) et lire ses propres
# secrets, un par un (Key Vault Secrets User sur chaque secret). Aucun mot de passe dans les conteneurs : Container
# Apps lit les secrets dans Key Vault avec l'identité du service.

locals {
  # Taille et exposition de chaque conteneur. Au plus 4 vCPU et 8 Gio par conteneur dans le plan consommation : c'est
  # ce que reçoit Ollama, sans GPU (environ 7 s par message sur 4 cœurs, mesuré par la CI). En veille sans visiteur
  # (min_replicas = 0) : rien n'est facturé, mais le premier message réveille Ollama et recharge le modèle.
  services = {
    "web"         = { port = 3000, cpu = 0.5, memoire = "1Gi", public = true }
    "portail-api" = { port = 8003, cpu = 0.25, memoire = "0.5Gi", public = false }
    "agent-api"   = { port = 8001, cpu = 0.5, memoire = "1Gi", public = false }
    "mcp-tools"   = { port = 8002, cpu = 0.25, memoire = "0.5Gi", public = false }
    "rag-faq"     = { port = 8004, cpu = 0.25, memoire = "0.5Gi", public = false }
    "bank-api"    = { port = 8000, cpu = 0.25, memoire = "0.5Gi", public = false }
    "ollama"      = { port = 11434, cpu = 4, memoire = "8Gi", public = false }
  }

  postgres = azurerm_postgresql_flexible_server.base.fqdn

  # Les variables d'environnement de chaque service : les mêmes que dans docker-compose.yml, adresses internes.
  variables = {
    "web" = {
      AGENT_API_URL   = "http://agent-api" # figées aussi dans l'image au build (apps/web/Dockerfile)
      PORTAIL_API_URL = "http://portail-api"
    }
    "portail-api" = {
      BANK_API_URL          = "http://bank-api"
      WAKIL_COOKIE_SECURISE = "1" # le site est en HTTPS : le cookie de session ne voyage jamais en clair
    }
    "agent-api" = {
      POSTGRES_HOST       = local.postgres
      AGENT_POSTGRES_USER = "wakil_agent"
      AGENT_POSTGRES_DB   = local.bases.agent
      MCP_TOOLS_URL       = "http://mcp-tools/mcp"
      MCP_FAQ_URL         = "http://rag-faq/mcp"
      OLLAMA_HOST         = "http://ollama"
      WAKIL_MODELE        = var.modele
    }
    "mcp-tools" = {
      BANK_API_URL        = "http://bank-api"
      MCP_HOTES_AUTORISES = "mcp-tools" # l'en-tête Host des appels d'agent-api (protection DNS rebinding)
    }
    "rag-faq" = {
      POSTGRES_HOST       = local.postgres
      FAQ_POSTGRES_USER   = "wakil_faq"
      FAQ_POSTGRES_DB     = local.bases.faq
      OLLAMA_HOST         = "http://ollama"
      MCP_HOTES_AUTORISES = "rag-faq"
    }
    "bank-api" = {
      POSTGRES_HOST = local.postgres
      POSTGRES_USER = "banque"
      POSTGRES_DB   = local.bases.banque
    }
    "ollama" = {
      OLLAMA_KEEP_ALIVE = "30m" # le modèle reste en mémoire tant que le conteneur vit
    }
  }

  # Les secrets de chaque service : variable d'environnement → nom du secret dans le coffre.
  secrets_des_services = {
    "web"         = {}
    "portail-api" = { WAKIL_JWT_CLE_PRIVEE = "session-cle-privee" }
    "agent-api"   = { AGENT_POSTGRES_PASSWORD = "postgres-agent-mdp", WAKIL_JWT_CLE_PUBLIQUE = "session-cle-publique" }
    "mcp-tools"   = { WAKIL_JWT_CLE_PUBLIQUE = "session-cle-publique", MCP_JWT_CLE_PRIVEE = "mcp-cle-privee" }
    "rag-faq"     = { FAQ_POSTGRES_PASSWORD = "postgres-faq-mdp" }
    "bank-api" = {
      POSTGRES_PASSWORD      = "postgres-banque-mdp"
      WAKIL_JWT_CLE_PUBLIQUE = "session-cle-publique"
      MCP_JWT_CLE_PUBLIQUE   = "mcp-cle-publique"
    }
    "ollama" = {}
  }

  # Une ligne par droit de lecture : « service/secret ».
  acces_aux_secrets = merge([
    for service, secrets in local.secrets_des_services : {
      for secret in toset(values(secrets)) : "${service}/${secret}" => { service = service, secret = secret }
    }
  ]...)
}

resource "azurerm_user_assigned_identity" "services" {
  for_each            = local.services
  name                = "id-${each.key}"
  resource_group_name = azurerm_resource_group.demo.name
  location            = azurerm_resource_group.demo.location
  tags                = local.etiquettes
}

resource "azurerm_role_assignment" "tire_ses_images" {
  for_each             = local.services
  scope                = azurerm_container_registry.images.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.services[each.key].principal_id
}

# Sur chaque secret, pas sur le coffre : agent-api ne peut pas lire la clé privée des sessions, même s'il est piraté.
resource "azurerm_role_assignment" "lit_ses_secrets" {
  for_each             = local.acces_aux_secrets
  scope                = azurerm_key_vault_secret.secrets[each.value.secret].resource_versionless_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.services[each.value.service].principal_id
}

resource "azurerm_container_app_environment" "demo" {
  name                       = "cae-${local.nom}"
  resource_group_name        = azurerm_resource_group.demo.name
  location                   = azurerm_resource_group.demo.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.journaux.id
  logs_destination           = "log-analytics"
  mutual_tls_enabled         = true # le trafic entre les conteneurs est chiffré par la plateforme
  tags                       = local.etiquettes

  # Le profil « Consumption » des environnements à profils : jusqu'à 4 vCPU et 8 Gio par conteneur (2 et 4 dans un
  # environnement sans profils), ce qu'il faut pour Ollama.
  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }
}

resource "azurerm_container_app" "services" {
  for_each                     = local.services
  name                         = each.key
  container_app_environment_id = azurerm_container_app_environment.demo.id
  resource_group_name          = azurerm_resource_group.demo.name
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"
  tags                         = local.etiquettes

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.services[each.key].id]
  }

  registry {
    server   = azurerm_container_registry.images.login_server
    identity = azurerm_user_assigned_identity.services[each.key].id
  }

  dynamic "secret" {
    for_each = toset(values(local.secrets_des_services[each.key]))
    content {
      name                = secret.value
      key_vault_secret_id = azurerm_key_vault_secret.secrets[secret.value].versionless_id
      identity            = azurerm_user_assigned_identity.services[each.key].id
    }
  }

  template {
    min_replicas = 0 # en veille quand personne ne s'en sert
    max_replicas = 1 # une seule copie : le quota de messages d'agent-api vit en mémoire (docs/securite.md)

    container {
      name   = each.key
      image  = "${azurerm_container_registry.images.login_server}/wakil/${each.key}:${var.version_images}"
      cpu    = each.value.cpu
      memory = each.value.memoire

      dynamic "env" {
        for_each = local.variables[each.key]
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.secrets_des_services[each.key]
        content {
          name        = env.key
          secret_name = env.value
        }
      }
    }
  }

  ingress {
    external_enabled = each.value.public
    target_port      = each.value.port
    # Le site n'accepte que HTTPS (le chat en a besoin : crypto.randomUUID). À l'intérieur, les services s'appellent en
    # http://nom, chiffré par le mutual TLS de l'environnement.
    allow_insecure_connections = !each.value.public
    transport                  = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  depends_on = [azurerm_role_assignment.tire_ses_images, azurerm_role_assignment.lit_ses_secrets]
}
