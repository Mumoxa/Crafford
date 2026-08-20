/* Oupa Attie — kuier */
(function () {
  const C = window.CRAFFORD;
  if (!C) return;

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const SEA_VOL = 0.38;

  const state = {
    filter: "all",
    album: [],
    voices: [],
    lightboxIndex: 0,
    sitIndex: 0,
    sitTimer: null,
    sitPaused: false,
    seaOn: false,
    currentAudio: null,
    currentVoice: null,
  };

  function init() {
    document.documentElement.classList.add("js");
    collectMedia();
    fillHero();
    renderLetter();
    renderTimeline();
    renderVoices();
    renderAlbum();
    renderLetters();
    initGate();
    initNav();
    initSound();
    initFilters();
    initLanterns();
    initGuestbook();
    initLightbox();
    initSit();
    initReveals();
    initWorlds();
    greetReturn();
    hideBrokenImages();
    upgradeLaughPhoto();
  }

  function upgradeLaughPhoto() {
    const bg = $("#laugh-bg");
    if (!bg) return;
    const src = "assets/photos/dans-wink.jpg";
    const test = new Image();
    test.onload = () => {
      bg.src = src;
      bg.alt = "Oupa Attie lag met hande in die lug";
    };
    test.src = src;
  }

  function collectMedia() {
    const album = [];
    const voices = [];
    const seen = new Set();

    function addPhoto(photo, memory) {
      if (!photo || !photo.src || seen.has(photo.src)) return;
      seen.add(photo.src);
      album.push({
        src: photo.src,
        caption: photo.caption || "",
        alt: photo.alt || photo.caption || C.name,
        year: photo.year || (memory && memory.year) || "",
        memory: memory ? memory.title : "",
      });
    }

    (C.photos || []).forEach((p) => addPhoto(p, null));
    sortedMemories(C.memories || []).forEach((m) => {
      (m.photos || []).forEach((p) => addPhoto(p, m));
      (m.voices || []).forEach((v) => {
        if (!v || !v.src) return;
        voices.push({ ...v, memory: m.title, landscape: m.landscape });
      });
    });

    state.album = album;
    state.voices = voices;
  }

  function memoryYear(m) {
    const y = String(m.year || "").match(/\d{4}/);
    return y ? y[0] : "";
  }

  function sortedMemories(list) {
    return list.slice().sort((a, b) => {
      const ay = memoryYear(a);
      const by = memoryYear(b);
      if (ay && by && ay !== by) return Number(ay) - Number(by);
      if (ay && !by) return 1;
      if (!ay && by) return -1;
      return (a.order || 0) - (b.order || 0);
    });
  }

  function fillHero() {
    const years = $(".hero-years");
    if (years) {
      years.textContent = C.years || "";
      years.classList.toggle("is-empty", !C.years);
    }
    const tag = $(".hero-tag");
    if (tag) tag.textContent = C.tagline;
    document.title = C.name + " · Kom kuier";
    if (C.portrait) {
      $$(".hero-portrait").forEach((img) => {
        img.src = C.portrait;
      });
    }
  }

  function renderLetter() {
    const hold = $("#letter-body");
    if (!hold) return;
    hold.innerHTML = "";
    (C.welcome || []).forEach((line) => {
      const p = document.createElement("p");
      p.textContent = line;
      hold.appendChild(p);
    });
  }

  function landscapeLabel(key) {
    return (
      {
        sea: "Die see",
        veld: "Die bosveld",
        laugh: "Sy lag",
        home: "Die stoep",
        family: "Familie",
        ride: "Motorfiets",
      }[key] || "Herinnering"
    );
  }

  function yearKey(m) {
    return memoryYear(m) || "Altyd";
  }

  function renderTimeline() {
    const track = $("#timeline-track");
    if (!track) return;
    const memories = sortedMemories(C.memories || []).filter(
      (m) => state.filter === "all" || m.landscape === state.filter
    );
    track.innerHTML = "";
    if (!memories.length) {
      track.innerHTML = '<p class="empty-hint">Nog geen herinneringe op hierdie deel van die pad nie.</p>';
      $("#year-nav") && ($("#year-nav").innerHTML = "");
      return;
    }

    const years = [];
    let last = null;
    memories.forEach((m) => {
      const y = yearKey(m);
      if (y !== last) {
        years.push(y);
        const mark = document.createElement("div");
        mark.className = "year-mark reveal";
        mark.id = "jaar-" + y.toLowerCase();
        mark.innerHTML = "<span>" + esc(y) + "</span>";
        track.appendChild(mark);
        last = y;
      }

      const art = document.createElement("article");
      art.className = "memory reveal";
      art.dataset.landscape = m.landscape || "home";
      art.id = "memory-" + m.id;

      const photos = (m.photos || [])
        .map((p) => {
          const i = state.album.findIndex((a) => a.src === p.src);
          return `<figure data-index="${i}">
            <img src="${esc(p.src)}" alt="${esc(p.alt || m.title)}" loading="lazy">
            ${p.caption ? `<figcaption>${esc(p.caption)}</figcaption>` : ""}
          </figure>`;
        })
        .join("");

      const videos = (m.videos || [])
        .filter((v) => v && v.src)
        .map(
          (v) => `<button class="video-card" data-video="${esc(v.src)}" data-title="${esc(v.title || m.title)}">
            ${v.poster ? `<img src="${esc(v.poster)}" alt="">` : `<video src="${esc(v.src)}#t=0.1" muted></video>`}
            <span><i class="play-orb" aria-hidden="true">▶</i> ${esc(v.title || "Speel video")}</span>
          </button>`
        )
        .join("");

      const voices = (m.voices || [])
        .filter((v) => v && v.src)
        .map((v) => {
          const idx = state.voices.findIndex((x) => x.src === v.src);
          return `<button class="track" data-voice="${idx}">
            <span class="track-index">◎</span>
            <span><b>${esc(v.title || "Stemnota")}</b><small>${esc(v.date || v.note || "Sy stem")}</small></span>
            <small>Speel</small>
          </button>`;
        })
        .join("");

      art.innerHTML = `
        <div class="memory-meta">
          <span class="memory-era">${esc(m.era || landscapeLabel(m.landscape))}</span>
          <span class="memory-date">${esc(m.dateLabel || m.year || "")}</span>
        </div>
        <h3>${esc(m.title)}</h3>
        ${m.story ? `<p class="memory-story">${esc(m.story)}</p>` : ""}
        ${photos ? `<div class="media-grid">${photos}</div>` : ""}
        ${videos ? `<div class="video-row">${videos}</div>` : ""}
        ${voices ? `<div class="voice-row">${voices}</div>` : ""}
      `;
      track.appendChild(art);
    });

    const nav = $("#year-nav");
    if (nav) {
      nav.innerHTML = years
        .map((y) => `<a href="#jaar-${esc(y.toLowerCase())}">${esc(y)}</a>`)
        .join("");
    }

    bindMediaClicks(track);
    hideBrokenImages();
    initReveals();
  }

  function bindMediaClicks(root) {
    $$(".media-grid figure", root).forEach((fig) => {
      fig.addEventListener("click", () => openLightbox(Number(fig.dataset.index) || 0));
    });
    $$("[data-video]", root).forEach((btn) => {
      btn.addEventListener("click", () => openVideo(btn.dataset.video, btn.dataset.title));
    });
    $$("[data-voice]", root).forEach((btn) => {
      btn.addEventListener("click", () => {
        document.getElementById("voice")?.scrollIntoView({ behavior: "smooth" });
        playVoice(Number(btn.dataset.voice));
      });
    });
  }

  function renderVoices() {
    const list = $("#playlist");
    const empty = $("#voice-empty");
    const radio = $("#radio");
    if (!list) return;

    if (!state.voices.length) {
      if (empty) empty.hidden = false;
      if (radio) radio.hidden = true;
      list.innerHTML = "";
      return;
    }

    if (empty) empty.hidden = true;
    if (radio) radio.hidden = false;

    list.innerHTML = state.voices
      .map(
        (v, i) => `<button class="track" data-play="${i}">
          <span class="track-index">${String(i + 1).padStart(2, "0")}</span>
          <span><b>${esc(v.title || "Stemnota")}</b><small>${esc(v.date || v.memory || "")}</small></span>
          <small>${esc(v.note || "")}</small>
        </button>`
      )
      .join("");

    $$("[data-play]", list).forEach((btn) => {
      btn.addEventListener("click", () => playVoice(Number(btn.dataset.play)));
    });

    buildWave();
    $("#play-main")?.addEventListener("click", toggleVoice);
    const seek = $("#seek");
    if (seek) {
      seek.addEventListener("input", () => {
        if (state.currentAudio && state.currentAudio.duration) {
          state.currentAudio.currentTime = (seek.value / 100) * state.currentAudio.duration;
        }
      });
    }
  }

  function buildWave() {
    const wave = $("#wave");
    if (!wave || wave.childElementCount) return;
    for (let i = 0; i < 42; i++) {
      const s = document.createElement("span");
      s.style.animationDelay = (i * 0.05).toFixed(2) + "s";
      s.style.height = 10 + ((i * 17) % 70) + "%";
      wave.appendChild(s);
    }
  }

  function playVoice(index) {
    const v = state.voices[index];
    if (!v) return;
    stopVoice();
    const audio = new Audio(v.src);
    state.currentAudio = audio;
    state.currentVoice = index;
    $("#radio-title").textContent = v.title || "Sy stem";
    $("#radio-note").textContent = [v.date, v.note, v.memory].filter(Boolean).join(" · ");
    const tr = $("#transcript");
    if (tr) {
      tr.textContent = v.transcript || "";
      tr.classList.toggle("is-on", Boolean(v.transcript));
    }
    $$("#playlist .track").forEach((t, i) => t.classList.toggle("is-current", i === index));
    $("#radio")?.classList.add("is-playing");
    setPlayIcon(true);
    duck(true);
    audio.addEventListener("timeupdate", () => {
      if (!audio.duration) return;
      $("#seek").value = String((audio.currentTime / audio.duration) * 100);
      $("#time").textContent = fmt(audio.currentTime) + " / " + fmt(audio.duration);
    });
    audio.addEventListener("ended", () => {
      $("#radio")?.classList.remove("is-playing");
      setPlayIcon(false);
      duck(false);
      if (index < state.voices.length - 1) playVoice(index + 1);
    });
    audio.play().catch(() => {});
  }

  function toggleVoice() {
    const a = state.currentAudio;
    if (!state.voices.length) return;
    if (!a) {
      playVoice(0);
      return;
    }
    if (a.paused) {
      a.play();
      $("#radio")?.classList.add("is-playing");
      setPlayIcon(true);
      duck(true);
    } else {
      a.pause();
      $("#radio")?.classList.remove("is-playing");
      setPlayIcon(false);
      duck(false);
    }
  }

  function stopVoice() {
    if (state.currentAudio) {
      state.currentAudio.pause();
      state.currentAudio.src = "";
      state.currentAudio = null;
    }
    $("#radio")?.classList.remove("is-playing");
    setPlayIcon(false);
  }

  function setPlayIcon(playing) {
    const btn = $("#play-main");
    if (!btn) return;
    btn.innerHTML = playing
      ? '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14"/><rect x="14" y="5" width="4" height="14"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
    btn.setAttribute("aria-label", playing ? "Pouseer" : "Speel");
  }

  function fmt(n) {
    if (!isFinite(n)) return "0:00";
    const m = Math.floor(n / 60);
    const s = Math.floor(n % 60);
    return m + ":" + String(s).padStart(2, "0");
  }

  function renderAlbum() {
    const hold = $("#masonry");
    if (!hold) return;
    hold.innerHTML = state.album
      .map(
        (p, i) => `<figure data-index="${i}">
          <img src="${esc(p.src)}" alt="${esc(p.alt)}" loading="lazy">
          <figcaption>${esc([p.year, p.caption].filter(Boolean).join(" — "))}</figcaption>
        </figure>`
      )
      .join("");
    $$("figure", hold).forEach((fig) => {
      fig.addEventListener("click", () => openLightbox(Number(fig.dataset.index)));
    });
  }

  function initFilters() {
    $$(".filter").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.filter = btn.dataset.filter;
        $$(".filter").forEach((b) => b.classList.toggle("is-on", b === btn));
        renderTimeline();
      });
    });
  }

  function initWorlds() {
    $$("[data-jump-filter]").forEach((el) => {
      el.addEventListener("click", () => {
        const f = el.getAttribute("data-jump-filter");
        state.filter = f;
        $$(".filter").forEach((b) => b.classList.toggle("is-on", b.dataset.filter === f));
        renderTimeline();
      });
    });
  }

  function initGate() {
    const gate = $("#gate");
    if (!gate) return;
    const close = () => {
      startSea();
      gate.classList.add("is-leaving");
      sessionStorage.setItem("attie-gate", "1");
      setTimeout(() => {
        gate.hidden = true;
      }, 1100);
    };
    const seen = sessionStorage.getItem("attie-gate") === "1";
    if (seen) {
      gate.hidden = true;
      startSea();
      return;
    }
    $("#gate-enter")?.addEventListener("click", close);
    gate.addEventListener("click", (e) => {
      if (e.target === gate) close();
    });
    document.addEventListener(
      "keydown",
      (e) => {
        if (e.key === "Enter" || e.key === " ") {
          if (!$("#gate")?.hidden) {
            e.preventDefault();
            close();
          }
        }
      },
      { once: true }
    );
  }

  function initNav() {
    const nav = $("#nav");
    const onScroll = () => {
      nav?.classList.toggle("is-solid", window.scrollY > 40);
      const ids = ["letter", "worlds", "timeline", "voice", "album", "stoep"];
      let current = "top";
      ids.forEach((id) => {
        const el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top < window.innerHeight * 0.45) current = id;
      });
      $$(".nav-links a, .dock a").forEach((a) => {
        const href = a.getAttribute("href") || "";
        a.classList.toggle("is-active", href === "#" + current);
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    $("#nav-toggle")?.addEventListener("click", () => {
      $("#nav-panel")?.classList.toggle("is-open");
    });
    $$("#nav-panel a").forEach((a) =>
      a.addEventListener("click", () => $("#nav-panel")?.classList.remove("is-open"))
    );
  }

  function initSound() {
    $$("[data-sound]").forEach((btn) => btn.addEventListener("click", toggleSea));
    ["pointerdown", "touchstart", "keydown"].forEach((ev) => {
      window.addEventListener(
        ev,
        () => {
          startSea();
        },
        { once: true, capture: true }
      );
    });
    startSea();
  }

  function seaEl() {
    return $("#see-audio");
  }

  function startSea() {
    const a = seaEl();
    if (!a) return;
    a.volume = SEA_VOL;
    const p = a.play();
    if (p && p.then) {
      p.then(() => {
        state.seaOn = true;
        markSound(true);
      }).catch(() => {
        markSound(false);
      });
    }
  }

  function toggleSea() {
    const a = seaEl();
    if (!a) return;
    if (a.paused) {
      startSea();
    } else {
      a.pause();
      state.seaOn = false;
      markSound(false);
    }
  }

  function duck(on) {
    const a = seaEl();
    if (!a) return;
    a.volume = on ? 0.08 : SEA_VOL;
  }

  function markSound(on) {
    $$("[data-sound]").forEach((b) => {
      b.classList.toggle("is-on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function initLightbox() {
    $("#lightbox-close")?.addEventListener("click", closeLightbox);
    $("#lightbox-prev")?.addEventListener("click", () => stepLightbox(-1));
    $("#lightbox-next")?.addEventListener("click", () => stepLightbox(1));
    $("#lightbox")?.addEventListener("click", (e) => {
      if (e.target.id === "lightbox") closeLightbox();
    });
    $("#video-close")?.addEventListener("click", closeVideo);
    document.addEventListener("keydown", (e) => {
      if ($("#lightbox")?.classList.contains("is-open")) {
        if (e.key === "Escape") closeLightbox();
        if (e.key === "ArrowRight") stepLightbox(1);
        if (e.key === "ArrowLeft") stepLightbox(-1);
      }
      if (e.key === "Escape") {
        closeVideo();
        closeSit();
      }
    });
  }

  function openLightbox(i) {
    if (!state.album.length) return;
    state.lightboxIndex = (i + state.album.length) % state.album.length;
    const item = state.album[state.lightboxIndex];
    const img = $("#lightbox-image");
    img.src = item.src;
    img.alt = item.alt;
    $("#lightbox-caption").textContent = [item.year, item.caption, item.memory].filter(Boolean).join("  ·  ");
    $("#lightbox").classList.add("is-open");
    document.body.classList.add("is-locked");
  }

  function stepLightbox(d) {
    openLightbox(state.lightboxIndex + d);
  }

  function closeLightbox() {
    $("#lightbox")?.classList.remove("is-open");
    document.body.classList.remove("is-locked");
  }

  function openVideo(src, title) {
    const modal = $("#video-modal");
    const vid = $("#video-el");
    if (!modal || !vid) return;
    vid.src = src;
    $("#video-caption").textContent = title || "";
    modal.classList.add("is-open");
    document.body.classList.add("is-locked");
    vid.play().catch(() => {});
  }

  function closeVideo() {
    const modal = $("#video-modal");
    const vid = $("#video-el");
    if (!modal) return;
    modal.classList.remove("is-open");
    if (vid) {
      vid.pause();
      vid.removeAttribute("src");
    }
    document.body.classList.remove("is-locked");
  }

  function initSit() {
    $$("[data-sit]").forEach((b) => b.addEventListener("click", openSit));
    $("#sit-close")?.addEventListener("click", closeSit);
    $("#sit-toggle")?.addEventListener("click", () => {
      state.sitPaused = !state.sitPaused;
      $("#sit-toggle").textContent = state.sitPaused ? "Speel" : "Pouseer";
    });
  }

  function openSit() {
    if (!state.album.length) return;
    $("#sit").classList.add("is-open");
    document.body.classList.add("is-locked");
    state.sitIndex = 0;
    state.sitPaused = false;
    showSit();
    clearInterval(state.sitTimer);
    state.sitTimer = setInterval(() => {
      if (state.sitPaused) return;
      state.sitIndex = (state.sitIndex + 1) % state.album.length;
      showSit();
    }, 7000);
  }

  function showSit() {
    const item = state.album[state.sitIndex];
    const frame = $("#sit-frame");
    if (!frame || !item) return;
    const img = document.createElement("img");
    img.src = item.src;
    img.alt = item.alt;
    frame.appendChild(img);
    requestAnimationFrame(() => img.classList.add("is-on"));
    const extras = $$("#sit-frame img");
    extras.forEach((el, i) => {
      if (i < extras.length - 1) {
        el.classList.remove("is-on");
        setTimeout(() => el.remove(), 1600);
      }
    });
    $("#sit-title").textContent = item.memory || C.name;
    $("#sit-cap").textContent = item.caption || C.epitaph;
    const bar = $("#sit-bar");
    if (bar) {
      bar.style.transition = "none";
      bar.style.width = "0%";
      requestAnimationFrame(() => {
        bar.style.transition = "width 7s linear";
        bar.style.width = "100%";
      });
    }
  }

  function closeSit() {
    $("#sit")?.classList.remove("is-open");
    clearInterval(state.sitTimer);
    document.body.classList.remove("is-locked");
  }

  function initLanterns() {
    const hold = $("#lanterns");
    if (!hold) return;
    const key = "attie-lanterns";
    let lit = [];
    try {
      lit = JSON.parse(localStorage.getItem(key) || "[]");
    } catch (e) {
      lit = [];
    }
    hold.innerHTML = "";
    for (let i = 0; i < 7; i++) {
      const b = document.createElement("button");
      b.className = "lantern" + (lit.includes(i) ? " is-lit" : "");
      b.type = "button";
      b.setAttribute("aria-label", "Steek ’n lantern aan vir Attie");
      b.addEventListener("click", () => {
        if (!lit.includes(i)) {
          lit.push(i);
          localStorage.setItem(key, JSON.stringify(lit));
          b.classList.add("is-lit");
          countLanterns(lit.length);
        }
      });
      hold.appendChild(b);
    }
    countLanterns(lit.length);
  }

  function countLanterns(n) {
    const el = $("#lantern-count");
    if (!el) return;
    if (!n) el.textContent = "Die lanterns wag. Steek een aan wanneer jy aan hom dink.";
    else if (n === 7) el.textContent = "Al sewe lanterns brand op hierdie stoep. Hy sou van die gloed gehou het.";
    else el.textContent = n + (n === 1 ? " lantern brand" : " lanterns brand") + " vir Oupa Attie op hierdie kuier.";
  }

  function renderLetters() {
    const hold = $("#letters");
    if (!hold) return;
    const saved = loadGuest();
    const all = [...(C.letters || []), ...saved];
    hold.innerHTML = all
      .map(
        (n) => `<article class="note-card">
          <div class="note-from">${esc(n.from || "Familie")}</div>
          <p class="note-text">${esc(n.text)}</p>
          <div class="note-date">${esc(n.date || "")}</div>
        </article>`
      )
      .join("");
  }

  function initGuestbook() {
    $("#guest-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      const from = $("#guest-from").value.trim();
      const text = $("#guest-text").value.trim();
      if (!from || !text) return;
      const letters = loadGuest();
      letters.unshift({
        from,
        text,
        date: new Date().toLocaleDateString("af-ZA", {
          day: "numeric",
          month: "long",
          year: "numeric",
        }),
      });
      localStorage.setItem("attie-letters", JSON.stringify(letters));
      e.target.reset();
      renderLetters();
    });
  }

  function loadGuest() {
    try {
      return JSON.parse(localStorage.getItem("attie-letters") || "[]");
    } catch (e) {
      return [];
    }
  }

  function initReveals() {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) {
            en.target.classList.add("is-in");
            io.unobserve(en.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    $$(".reveal").forEach((el) => io.observe(el));
  }

  function greetReturn() {
    const key = "attie-visited";
    const was = localStorage.getItem(key);
    localStorage.setItem(key, "1");
    if (was) {
      const k = $("#gate-kicker");
      if (k) k.textContent = "Welkom terug";
    }
  }

  function hideBrokenImages() {
    $$("img").forEach((img) => {
      if (img.dataset.errBound) return;
      img.dataset.errBound = "1";
      img.addEventListener("error", () => {
        const fig = img.closest("figure");
        if (fig) fig.style.display = "none";
        if (img.classList.contains("hero-portrait")) img.style.display = "none";
        if (img.classList.contains("laugh-bg")) img.src = "assets/images/firelight.jpg";
      });
    });
  }

  function esc(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
