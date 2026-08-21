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

## Deel ’n foto of video (die familie-vak)

Die **Deel**-bladsy op die werf stuur familie na die [`uploads/`](uploads/)-gids:
laai enige foto, video of stemnota op (GitHub web → *Add file → Upload files → Commit*).

Daarna word dit outomaties gesorteer en op die tydlyn gesit:

```bash
python3 scripts/import-contributions.py          # lees uploads/, skryf js/contributions.js
```

- ’n datum in die lêernaam (`IMG-20210412-WA0020`, `20120804_100209`, `04-08-2012`) of in die EXIF → regte plek op die tydlyn, gegroepeer per maand as *Gedeel deur die familie*
- geen datum nie → *Datum onbekend* agteraan
- video’s kom by daardie maand se herinnering, stemnotas by **Sy stem**
- die 21 oorspronklike foto-name (sien `scripts/import-photos.py`) word steeds direk op die hoof-tydlyn ingepas

**Eenmalige outomatisering:** plak [`scripts/outomatiese-invoer.yml.txt`](scripts/outomatiese-invoer.yml.txt) as `.github/workflows/invoer.yml` (GitHub web → *Add file → Create new file*). Daarna loop die invoer self elke keer as iemand iets in `uploads/` laai.

WhatsApp- en e-pos kaarte op die Deel-bladsy verskyn sodra `contribute.whatsapp` / `contribute.email` in [`js/content.js`](js/content.js) gevul word.

## Foto’s, video’s, stemnotas

Alles leef in [`js/content.js`](js/content.js) (en bydraes in `js/contributions.js`).

| Soort      | Gids               |
| ---------- | ------------------ |
| Foto’s     | `assets/photos/`   |
| Video’s    | `assets/videos/`   |
| Stemnotas  | `assets/voices/`   |
| Bydraes    | `uploads/`         |

Die tydlyn sorteer volgens jaar. Sit `year: "2012"` en `dateLabel: "4 Augustus 2012"` by ’n herinnering.

## Kamers

- **Kuier** — die brief, twee stoele
- **Die see / Die bosveld**
- **Tydlyn** — sy foto’s, in volgorde
- **Sy stem** — stemnotas
- **Album**
- **Die stoep** — lanterns en woorde
- **Sit by hom** — stil skyfievertoning
