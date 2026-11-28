# ADR 0005 — Le déploiement sur Azure : Container Apps, Ollama sur CPU, et aucun secret dans l'état Terraform

- **Statut** : acceptée, code écrit et vérifié en CI ; **pas encore appliquée** (aucun compte Azure pour l'instant)
- **Date** : 27/11/2026

## Contexte

Wakil tourne en local en six conteneurs (profil `images` de `docker-compose.yml`), plus Ollama sur le PC. Pour une démo
en ligne, il faut :

- **un budget proche de zéro** : un compte gratuit Azure (crédit de départ, puis paiement à l'usage), sans GPU ;
- **les mêmes frontières de sécurité qu'en local** : seul le site est public, chaque service ne reçoit que ses secrets,
  la banque n'accepte que des jetons signés ([ADR 0004](0004-jetons-entre-services.md)) ;
- **des modèles locaux seulement** ([ADR 0003](0003-choix-des-modeles.md)) : `qwen3:4b-instruct` et `bge-m3` dans Ollama ;
- **une infrastructure décrite en code**, vérifiable sans compte, et qu'on peut détruire et recréer d'une commande.

## Décision

Le code est dans [`infra/terraform/`](../../infra/terraform/), en deux modules :

| Module | Contenu | Quand le détruire |
|---|---|---|
| `bootstrap` | Le stockage de l'état Terraform (sans clé partagée, versions gardées 30 jours) et l'alerte de budget (50, 80, 100 % et prévision) | Jamais |
| `environnement` | Registre d'images, Key Vault, PostgreSQL Flexible (pgvector, 3 bases), Log Analytics plafonné, environnement Container Apps et 7 conteneurs | Après chaque démonstration |

**Les conteneurs** : Azure Container Apps, plan consommation avec le profil « Consumption », `min_replicas = 0`.

| Conteneur | Taille | Exposition |
|---|---|---|
| `web` | 0,5 vCPU, 1 Gio | **public, HTTPS seulement** |
| `portail-api`, `mcp-tools`, `rag-faq`, `bank-api` | 0,25 vCPU, 0,5 Gio | internes |
| `agent-api` | 0,5 vCPU, 1 Gio | interne, **une seule copie** (le quota de messages vit en mémoire) |
| `ollama` | **4 vCPU, 8 Gio** (le maximum du plan, sans GPU) | interne |

**Les secrets ne passent jamais par l'état Terraform.** Le piège classique : un mot de passe généré par Terraform est
écrit en clair dans son fichier d'état. Ici, les mots de passe PostgreSQL et les deux paires de clés RS256 sont générés
par des ressources **éphémères** (elles n'existent que pendant le passage de Terraform) et envoyés à Azure par des
arguments en **écriture seule** (`value_wo`, `administrator_password_wo`) : Azure les reçoit, Terraform ne les garde pas.
Pour les faire tourner : augmenter `version_des_secrets`.

**Le moindre privilège, secret par secret.** Chaque conteneur a sa propre identité managée, avec deux droits seulement :
tirer ses images (`AcrPull`) et lire **ses** secrets, un par un (`Key Vault Secrets User` sur chaque secret, pas sur le
coffre). `agent-api` ne peut pas lire la clé privée des sessions, même s'il est piraté.

**Le réseau.** Le site n'accepte que HTTPS : le chat en a besoin (`crypto.randomUUID` n'existe que sur une page sûre,
voir [les captures](../developpement.md#les-captures-décran-du-readme)). À l'intérieur, les services s'appellent par leur
nom (`http://bank-api`), et l'environnement chiffre ce trafic (mutual TLS). Les serveurs MCP acceptent leur nom interne
(`MCP_HOTES_AUTORISES`), sans couper leur protection contre le DNS rebinding.

## Pourquoi

- **Container Apps plutôt qu'AKS** : pas de cluster à payer ni à maintenir, mise en veille à zéro, HTTPS et identités
  managées compris. Microsoft décrit AKS comme orienté contrôle, avec une « courbe d'apprentissage significative ».
- **Plutôt qu'une VM** : les VM gratuites (B1s, B2pts v2, B2ats v2) n'ont qu'1 Gio de mémoire, trop peu pour qwen3:4b
  (environ 3,5 Go). Une VM plus grande facturerait chaque heure, même sans visiteur.
- **Ollama sur CPU** : un GPU demande un profil dédié, hors budget. Sur 4 cœurs, la CI mesure environ 7 s par question
  (113 questions en 16 minutes, installation comprise).
- **Les secrets éphémères** : c'est la façon la plus simple de tenir la règle « aucun secret dans le dépôt ni dans un
  fichier », Key Vault compris.

## Les écarts assumés avec une production

Trivy (`trivy config`, bloquant en CI) ne trouve plus aucun écart non justifié. Ceux qui restent sont écrits dans le
code, au-dessus de leur ressource (`#trivy:ignore`) :

| Écart | Pourquoi, pour la démo | En production |
|---|---|---|
| PostgreSQL, Key Vault et le stockage de l'état joignables par Internet (protégés par Entra ID, mot de passe et TLS) | Le plan consommation n'a pas d'adresse fixe ; un réseau privé coûte plus que la démo | Réseau virtuel et points de terminaison privés |
| Règle de pare-feu « services Azure » (0.0.0.0) sur PostgreSQL | Même raison : elle laisse passer tout service Azure, pas seulement les nôtres | Réseau privé, ou identité Entra ID pour la base |
| Pas de protection contre la purge de Key Vault | La démo est détruite et recréée avec le même nom | Purge interdite |
| Clés de chiffrement gérées par Microsoft, une seule région | Coût et simplicité | Clés gérées par la banque, réplication géographique |
| Pas de date d'expiration sur les secrets | Un secret expiré couperait la démo sans prévenir | Expiration et rotation automatiques |

## Ce qui reste à faire (morceaux 25 à 27, avec un compte)

1. **L'image d'Ollama** avec ses deux modèles (environ 4 Go) : l'image officielle pèse 3,8 Go à elle seule, parce
   qu'elle embarque les bibliothèques GPU ; en chercher une plus légère pour le CPU.
2. **Un job d'initialisation** (Container Apps Job) qui rejoue les scripts du dépôt avec les mots de passe de Key Vault :
   rôles PostgreSQL (`schema.sql`, `base-agent.sh`, `base-faq.sh`), données fictives, index de la FAQ.
3. **Le pipeline** : GitHub → Azure sans secret (OIDC), images poussées dans le registre, `terraform plan` affiché dans la
   PR, `apply` après approbation, nouvelle révision testée avant de recevoir les visiteurs.
4. **Mesurer le coût réel.** Estimation, à vérifier : les conteneurs restent dans l'allocation gratuite mensuelle de
   Container Apps (180 000 vCPU-secondes, soit environ 12 heures d'Ollama par mois) ; PostgreSQL B1MS et le registre sont
   gratuits 12 mois pour un nouveau compte ; Key Vault, Log Analytics (plafonné à 0,1 Go par jour) et le stockage de
   l'état coûtent quelques centimes.

## Conséquences

- **Le premier message après une mise en veille est lent** : Ollama redémarre et recharge le modèle. À mesurer.
- **Une seule copie d'agent-api** tant que le quota vit en mémoire ; un compteur partagé (ou une passerelle) permettra
  d'en avoir plusieurs.
- **Un serveur PostgreSQL arrêté redémarre tout seul au bout de 7 jours** (limite d'Azure) : la démo se détruit plutôt
  qu'elle ne s'arrête.
- Les **adresses internes sont figées dans l'image du site** au build (`AGENT_API_URL`, `PORTAIL_API_URL`) : sur Azure
  `http://agent-api` et `http://portail-api`, sans port, contre `http://agent-api:8001` dans compose. Le pipeline
  construira donc l'image du site pour Azure avec ses propres adresses.
