"""La FAQ de la Banque Atlas Démo : retrouver la fiche qui répond à la question du client, pour la citer telle quelle.

Un modèle d'embeddings (bge-m3, dans Ollama) transforme chaque phrase en vecteur : deux phrases de même sens donnent
des vecteurs proches. Les vecteurs des fiches (data/faq/faq.yaml : titre et texte, plus chaque question type en
darija) sont rangés avec pgvector dans la base de la FAQ (wakil_faq), qui n'appartient qu'à ce service : l'agent n'y a
aucun accès. Pour une question, on calcule son vecteur et on prend la fiche la plus proche ; sous le seuil, aucune
fiche : Wakil le dit au lieu d'inventer.

Aucun type MCP ici (serveur.py fait le branchement) : ces fonctions servent aussi à l'indexation et à la mesure.
Indexer (depuis apps/rag-faq, base et Ollama démarrés) : uv run --env-file ../../.env python -m app.faq
"""

import atexit
import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from langchain_ollama import OllamaEmbeddings
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

FICHIER = Path(__file__).resolve().parents[3] / "data" / "faq" / "faq.yaml"
MODELE = os.environ.get("WAKIL_EMBEDDINGS", "bge-m3")
# Similarité cosinus minimale (1 = même sens, 0 = sans rapport). Choisie sur les mesures : evals/faq/resultats.md.
SEUIL = 0.6

# Le type « vector » sans taille : chaque modèle a la sienne (1024 nombres pour bge-m3), et la colonne modele dit
# lequel a produit chaque vecteur. Avec une centaine de vecteurs, PostgreSQL les compare tous en une fraction de
# milliseconde : pas besoin d'index (HNSW) avant des dizaines de milliers.
SCHEMA = [
    """CREATE TABLE IF NOT EXISTS faq_fiches (
        id     TEXT PRIMARY KEY,
        titre  TEXT NOT NULL,
        texte  TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS faq_vecteurs (
        fiche_id   TEXT NOT NULL REFERENCES faq_fiches (id) ON DELETE CASCADE,
        phrase     TEXT NOT NULL,
        modele     TEXT NOT NULL,
        embedding  vector NOT NULL
    )""",
]


class FaqIndisponible(Exception):
    """La base de la FAQ, pgvector ou le modèle d'embeddings ne répond pas, ou la FAQ n'est pas indexée."""


@dataclass(frozen=True)
class Trouvaille:
    fiche: str
    titre: str
    texte: str
    similarite: float


_pool: ConnectionPool | None = None


def base() -> ConnectionPool:
    """Le pool de connexions vers la base de la FAQ, ouvert à la première demande ; crée les tables si besoin."""
    global _pool
    if _pool is None:
        if "FAQ_POSTGRES_USER" not in os.environ:
            raise FaqIndisponible("base de la FAQ non configurée (FAQ_POSTGRES_* dans .env)")
        conninfo = make_conninfo(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            user=os.environ["FAQ_POSTGRES_USER"],
            password=os.environ["FAQ_POSTGRES_PASSWORD"],
            dbname=os.environ["FAQ_POSTGRES_DB"],
        )
        pool = ConnectionPool(
            conninfo,
            kwargs={"autocommit": True, "row_factory": dict_row},
            check=ConnectionPool.check_connection,  # survit à un redémarrage de PostgreSQL
            open=True,
        )
        with pool.connection() as conn:
            if conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'").fetchone() is None:
                pool.close()
                raise FaqIndisponible("pgvector n'est pas activé : relancer base-faq.sh (voir le README)")
            for requete in SCHEMA:
                conn.execute(requete)
        atexit.register(pool.close)
        _pool = pool
    return _pool


def lire_fiches(fichier: Path = FICHIER) -> list[dict]:
    return yaml.safe_load(fichier.read_text(encoding="utf-8"))


def _vecteur(nombres: list[float]) -> str:
    """Un vecteur tel que pgvector le lit dans une requête : « [0.028,-0.01,…] »."""
    return "[" + ",".join(map(str, nombres)) + "]"


def _embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=MODELE)


def indexer(fiches: list[dict] | None = None) -> tuple[int, int]:
    """Calcule les vecteurs de toutes les fiches et remplace l'index de ce modèle, en une seule transaction."""
    fiches = fiches if fiches is not None else lire_fiches()
    phrases = [(f["id"], f"{f['titre']}. {f['texte']}") for f in fiches]
    phrases += [(f["id"], question) for f in fiches for question in f["questions"]]
    vecteurs = _embeddings().embed_documents([phrase for _, phrase in phrases])
    with base().connection() as conn, conn.transaction():
        conn.execute("DELETE FROM faq_fiches WHERE NOT (id = ANY(%s))", ([f["id"] for f in fiches],))
        for f in fiches:
            conn.execute(
                "INSERT INTO faq_fiches (id, titre, texte) VALUES (%s, %s, %s) "
                "ON CONFLICT (id) DO UPDATE SET titre = EXCLUDED.titre, texte = EXCLUDED.texte",
                (f["id"], f["titre"], f["texte"]),
            )
        conn.execute("DELETE FROM faq_vecteurs WHERE modele = %s", (MODELE,))
        conn.cursor().executemany(
            "INSERT INTO faq_vecteurs (fiche_id, phrase, modele, embedding) VALUES (%s, %s, %s, %s::vector)",
            [(fiche_id, phrase, MODELE, _vecteur(v)) for (fiche_id, phrase), v in zip(phrases, vecteurs, strict=True)],
        )
    return len(fiches), len(phrases)


def classer(question: str, nombre: int = 3) -> list[Trouvaille]:
    """Les fiches les plus proches de la question, de la plus proche à la moins proche.

    Une fiche a plusieurs vecteurs (son texte, ses questions types) : elle prend le score du plus proche.
    """
    pool = base()  # d'abord la base : sans elle, inutile de faire calculer un vecteur à Ollama
    try:
        vecteur = _vecteur(_embeddings().embed_query(question))
        with pool.connection() as conn:
            lignes = conn.execute(
                """
                SELECT f.id, f.titre, f.texte, max(1 - (v.embedding <=> %(q)s::vector)) AS similarite
                FROM faq_vecteurs v JOIN faq_fiches f ON f.id = v.fiche_id
                WHERE v.modele = %(modele)s
                GROUP BY f.id, f.titre, f.texte
                ORDER BY similarite DESC
                LIMIT %(nombre)s
                """,
                {"q": vecteur, "modele": MODELE, "nombre": nombre},
            ).fetchall()
    except Exception as panne:  # Ollama arrêté, base injoignable…
        raise FaqIndisponible(str(panne)) from panne
    if not lignes:
        raise FaqIndisponible(f"FAQ non indexée pour le modèle {MODELE} : lancer python -m app.faq")
    return [Trouvaille(ligne["id"], ligne["titre"], ligne["texte"], float(ligne["similarite"])) for ligne in lignes]


def chercher(question: str) -> Trouvaille | None:
    """La fiche qui répond à la question, ou None si aucune n'est assez proche (sous le seuil)."""
    meilleure = classer(question, 1)[0]
    return meilleure if meilleure.similarite >= SEUIL else None


if __name__ == "__main__":
    nb_fiches, nb_vecteurs = indexer()
    print(f"FAQ indexée avec {MODELE} : {nb_fiches} fiches, {nb_vecteurs} vecteurs.")
