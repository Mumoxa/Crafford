# Oupa Attie Crafford

’n Plek om te kuier wanneer jy hom mis.

Liefhebber van die see, die bosveld, en ’n lag wat ’n huis kon volmaak.

## GitHub Pages

Live: <https://mumoxa.github.io/Crafford/>

As die skakel nog nie oopmaak nie (die repo is tans privaat):

1. GitHub → **Settings** → **General** → maak die repo **Public**
2. **Settings** → **Pages** → Source: **GitHub Actions**
   (of *Deploy from a branch* → `main` → `/ (root)`)

Die werkvloei in `.github/workflows/pages.yml` sit die stoep dan uit.

## Maak oop

```bash
python3 -m http.server 8080
```

Die see speel sag in die agtergrond. Op ’n foon: sit dit op die tuisskerm — dit maak oop soos ’n huis, nie ’n blaaier-oortjie nie.

## Foto’s, video’s, stemnotas

Alles leef in [`js/content.js`](js/content.js).

| Soort      | Gids               |
| ---------- | ------------------ |
| Foto’s     | `assets/photos/`   |
| Video’s    | `assets/videos/`   |
| Stemnotas  | `assets/voices/`   |

Die tydlyn sorteer volgens jaar. Sit `year: "2012"` en `dateLabel: "4 Augustus 2012"` by ’n herinnering.

## Kamers

- **Kuier** — die brief, twee stoele
- **Die see / Die bosveld**
- **Tydlyn** — sy foto’s, in volgorde
- **Sy stem** — stemnotas
- **Album**
- **Die stoep** — lanterns en woorde
- **Sit by hom** — stil skyfievertoning
