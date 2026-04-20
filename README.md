# Notiosint

Notiosint est un outil de reconnaissance OSINT ciblant les pages Notion publiques. À partir d'une URL ou d'un ID de page, il énumère les utilisateurs ayant contribué à cette page et récupère leurs informations — nom, email, user ID — sans aucune authentification.

## Contexte

L'API interne de Notion (`/api/v3/`) expose sur les pages publiques les `user_id` de tous les contributeurs via `loadPageChunk`. Ces IDs peuvent ensuite être résolus en profils complets (nom + email) via `syncRecordValuesMain`. Pas vraiment un bug, plutôt une exposition d'informations non filtrée sur les espaces publics. Ce script automatise cette chaîne.

## Setup

```bash
python3 -m venv dep
source ./dep/bin/activate
pip install requests
python notiosint.py
```


## Usage

Le script accepte une URL Notion complète ou un ID de page brut (avec ou sans tirets, il normalise) :

```
Enter Notion URL or Page ID: https://monespace.notion.site/ma-page-abc123
```

```
Enter Notion URL or Page ID: abc1234567890abcdef1234567890ab
```

Output typique :

```
[+] Page ID Extracted : abc12345-6789-0abc-def1-234567890abc
[+] User IDs found: ['uid1', 'uid2', ...]
[+] Users found:

- ID: uid1
  Name: Jean Dupont
  Email: jean.dupont@example.com
```

## Fonctionnement

Le script enchaîne trois appels à l'API interne Notion :

1. **`getPublicPageDataForDomain`** — résout le slug/domaine en `pageId` (seulement si une URL est passée)
2. **`loadPageChunk`** — charge les blocs de la page (limit: 100, chunk 0), puis crawl récursivement le JSON pour extraire tous les champs `user_id`
3. **`syncRecordValuesMain`** — batch request pour résoudre chaque user ID en profil `notion_user` complet

Les trois endpoints sont non documentés mais stables. Le User-Agent est spoofé en `Mozilla/5.0` par précaution, Notion ne semble pas vraiment filtrer sur ce critère.

## Limitations

- Fonctionne uniquement sur les pages **publiquement accessibles**
- Un seul chunk chargé (`chunkNumber: 0`, `limit: 100`) — sur les pages très longues, des user IDs peuvent passer à la trappe
- Aucune gestion de la pagination/cursor pour l'instant
- L'email n'est pas systématiquement présent (dépend des paramètres de confidentialité du compte Notion)
- Si Notion modifie le format de ces endpoints, le script casse

## Notes

Testé sur des workspaces publics : blogs, portfolios, docs open-source. À utiliser uniquement dans un cadre légal, sur des cibles pour lesquelles une autorisation a été obtenue.
