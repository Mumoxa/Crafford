/* ============================================================
 *  FAMILIE-BYDRAES
 * ============================================================ */

window.CRAFFORD_CONTRIB = {
  memories: [
    {
      id: "stemnota-2018-12-26",
      dateLabel: "26 Desember 2018",
      year: "2018",
      order: 1,
      era: "Sy stem",
      landscape: "family",
      title: "Voicenotes van Pa",
      story: "'n Stemnota van Pa, op 26 Desember 2018.",
      photos: [],
      videos: [],
      voices: [
        {
          src: "uploads/Voicenotes van Pa 26 Desember 2018.oga",
          title: "Voicenotes van Pa",
          date: "26 Desember 2018",
          note: "Stemnota van Pa"
        }
      ]
    },
    {
      id: "boeremusiek-stokkie",
      dateLabel: "Datum onbekend",
      year: "",
      order: 2,
      era: "Sy stem",
      landscape: "family",
      title: "Pa en sy Boeremusiek stokkie",
      story: "Pa en sy Boeremusiek stokkie.",
      photos: [],
      videos: [],
      voices: [
        {
          src: "uploads/Pa en sy Boeremusiek stokkie.oga",
          title: "Pa en sy Boeremusiek stokkie",
          date: "Datum onbekend",
          note: "Stemnota van Pa"
        }
      ]
    }
  ]
};

if (window.CRAFFORD && Array.isArray(window.CRAFFORD.memories)) {
  window.CRAFFORD.memories.push(...window.CRAFFORD_CONTRIB.memories);
}
