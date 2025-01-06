# Mihon Tracker Importer

This is a tool to track manga entries on your favorite manga tracker.

## Requirements

- Python 3.12
- Pipenv

Create a `.env` file with the following variables:

```env
MAL_CLIENT_ID=
MAL_CLIENT_SECRET=
```

## Installation

```bash
pipenv install
```

## Usage

```bash
make run #(or make dev to run in dev mode)
```

## Trackers

> ( ✅ = Implemented, ❌ = Not Implemented, ⚠️ = Partial Implementation)

- [MAL](https://myanimelist.net/) - MyAnimeList ✅⚠️ (Works but needs some tweaking)
- [AniList](https://anilist.co/) - AniList ❌
- [Kitsu](https://kitsu.io/) - Kitsu ❌
- [MangaUpdates](https://mangaupdates.com/) - MangaUpdates ❌
- [Shikimori](https://shikimori.one/) - Shikimori ❌
- [Bangumi](https://bangumi.tv/) - Bangumi ❌
