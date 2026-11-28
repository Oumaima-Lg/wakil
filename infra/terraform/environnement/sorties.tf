output "adresse_du_site" {
  description = "L'adresse publique de la démo (HTTPS)."
  value       = "https://${azurerm_container_app.services["web"].ingress[0].fqdn}"
}

output "registre" {
  description = "Le registre où le pipeline pousse les images (wakil/<service>:<version>)."
  value       = azurerm_container_registry.images.login_server
}

output "coffre" {
  value = azurerm_key_vault.secrets.name
}

output "postgres" {
  value = azurerm_postgresql_flexible_server.base.fqdn
}

output "groupe_de_ressources" {
  value = azurerm_resource_group.demo.name
}
