// THE LAST LIGHT · презентация за защита. Без библиотеки, без интернет.
// Клавиши: → / Space / клик = напред (следваща стъпка, после слайд) · ← = назад · Home/End · F цял екран
//          N бележки за говорене · T таймер · Esc спира видеото / затваря бележките · #5 в адреса отваря слайд 5
(function () {
  const stage = document.getElementById('stage');
  const slides = Array.from(document.querySelectorAll('.slide'));
  const notesEl = document.getElementById('notes');
  const timerEl = document.getElementById('timer');
  let cur = 0, step = 0, t0 = null, tick = null;

  function fit() {
    const s = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    stage.style.transform = 'scale(' + s + ')';
  }
  function maxStep(i) {
    let m = 0;
    slides[i].querySelectorAll('[data-step]').forEach(e => { m = Math.max(m, +e.dataset.step); });
    if (slides[i].querySelector('video')) m = Math.max(m, 1);
    return m;
  }
  function apply() {
    slides.forEach((s, i) => s.classList.toggle('on', i === cur));
    slides[cur].querySelectorAll('[data-step]').forEach(e => e.classList.toggle('vis', +e.dataset.step <= step));
    slides[cur].querySelectorAll('[data-hide]').forEach(e => e.classList.toggle('gone', step >= +e.dataset.hide));
    slides[cur].querySelectorAll('[data-only]').forEach(e => e.classList.toggle('only-off', step !== +e.dataset.only));
    slides[cur].querySelectorAll('[data-case]').forEach(e => e.classList.toggle('selected', step === +e.dataset.case));
    slides[cur].classList.toggle('playing', !!slides[cur].querySelector('video') && step >= 1);
    slides[cur].classList.toggle('demonstrated', step >= 1);
    slides.forEach((s, i) => { if (i !== cur) s.querySelectorAll('video').forEach(v => v.pause()); });
    const vid = slides[cur].querySelector('video');
    if (vid) {
      if (step >= 1) { if (vid.paused && !vid.ended) vid.play().catch(() => {}); }
      else { vid.pause(); vid.currentTime = 0; }
    }
    const n = slides[cur].querySelector('.notes');
    notesEl.innerHTML = '<div class="h">Слайд ' + (cur + 1) + ' / ' + slides.length + ' · ' + (slides[cur].dataset.sec || '') + ' с</div>' + (n ? n.innerHTML : '');
    history.replaceState(null, '', '#' + (cur + 1));
    document.title = 'The Last Light · защита (' + (cur + 1) + '/' + slides.length + ')';
  }
  function next() {
    if (step < maxStep(cur)) step++;
    else if (cur < slides.length - 1) { cur++; step = 0; }
    apply();
  }
  function prev() {
    if (step > 0) step--;
    else if (cur > 0) { cur--; step = maxStep(cur); }
    apply();
  }
  function go(i) { cur = Math.max(0, Math.min(slides.length - 1, i)); step = 0; apply(); }
  function startTimer() {
    if (t0 === null) { t0 = Date.now(); tick = setInterval(() => {
      const s = Math.floor((Date.now() - t0) / 1000);
      timerEl.textContent = String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
    }, 500); }
  }
  // Български надписи за клипа, вградени (a <track> от file:// не се зарежда в Chromium)
  const CUES = [[2.1, 4.83, 'Разследването реши, че вината е на капитана ѝ.'], [5.2, 7.4, 'В дневника на фара пишеше, че светлината е горяла.'],
    [7.7, 10.67, 'Знам какво пишеше в дневника… Аз го написах.'], [12.9, 16.13, 'Тази нощ – същата буря. Същият канал.'],
    [17.9, 21.72, 'И някой там, в морето, се обажда като „Мери Елън“.']];
  const vEl = document.querySelector('video'), subs = document.getElementById('subs');
  if (vEl && subs) {
    const upd = () => { const c = CUES.find(q => vEl.currentTime >= q[0] && vEl.currentTime <= q[1]); subs.textContent = (!vEl.paused || vEl.currentTime > 0) && c ? c[2] : ''; };
    ['timeupdate', 'seeked', 'play', 'pause', 'ended'].forEach(ev => vEl.addEventListener(ev, upd));
  }
  window.addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.target.closest('a,button,input,textarea,select,video') && ['Enter', ' '].includes(e.key)) return;
    switch (e.key) {
      case 'ArrowRight': case 'ArrowDown': case 'PageDown': case ' ': case 'Enter': e.preventDefault(); startTimer(); next(); break;
      case 'ArrowLeft': case 'ArrowUp': case 'PageUp': case 'Backspace': e.preventDefault(); prev(); break;
      case 'Home': go(0); break;
      case 'End': go(slides.length - 1); break;
      case 'f': case 'F': if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(() => {}); break;
      case 'n': case 'N': notesEl.classList.toggle('on'); break;
      case 't': case 'T': timerEl.classList.toggle('on'); startTimer(); break;
      case 'Escape': notesEl.classList.remove('on'); slides[cur].querySelectorAll('video').forEach(v => v.pause()); break;
    }
  });
  stage.addEventListener('click', e => { if (e.target.closest('video,a,button,input,textarea,select')) return; startTimer(); next(); });
  slides.forEach((s, i) => { const num = document.createElement('div'); num.className = 'num'; num.textContent = (i + 1) + ' / ' + slides.length; s.appendChild(num); });
  window.addEventListener('resize', fit);
  fit();
  const h = parseInt((location.hash || '').slice(1), 10);
  if (h >= 1 && h <= slides.length) cur = h - 1;
  apply();
  // for the rehearsal script
  window.__deck = { go, next, prev, state: () => ({ cur, step, max: maxStep(cur), total: slides.length }), setStep: n => { step = n; apply(); } };
})();
