# Les valeurs à reporter dans la configuration du backend de l'environnement (environnement/etat.tfbackend).
output "groupe_de_ressources" {
  value = azurerm_resource_group.etat.name
}

output "compte_de_stockage" {
  value = azurerm_storage_account.etat.name
}

output "conteneur" {
  value = azurerm_storage_container.etat.name
}
