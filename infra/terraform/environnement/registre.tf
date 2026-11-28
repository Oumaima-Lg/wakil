# Le registre des images de Wakil (l'équivalent d'ECR chez AWS). Ni compte administrateur ni accès anonyme : les
# conteneurs tirent leurs images avec leur identité (rôle AcrPull, voir applications.tf), le pipeline avec la sienne.
resource "azurerm_container_registry" "images" {
  name                   = "acrwakil${random_string.suffixe.result}"
  resource_group_name    = azurerm_resource_group.demo.name
  location               = azurerm_resource_group.demo.location
  sku                    = "Standard" # gratuit 12 mois pour un nouveau compte ; « Premium » seul ferme le réseau public
  admin_enabled          = false
  anonymous_pull_enabled = false
  tags                   = local.etiquettes
}
