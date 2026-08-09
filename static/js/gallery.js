/* Qualitative comparison gallery.
 *
 * The point of this component is that switching methods must not move or reload
 * anything: all four renders for the current scene sit stacked in the stage and
 * only their opacity changes. Changing scene is the only thing that touches the
 * DOM, and it preloads the neighbours so paging through stays instant.
 */
(function () {
  const root = document.getElementById('gallery');
  if (!root || typeof QUALITATIVE === 'undefined') return;

  const METHODS = ['atiss', 'diff', 'inst', 'ours'];
  const LABELS = {
    atiss: 'ATISS', diff: 'DiffuScene', inst: 'InstructScene', ours: 'SceneNAT',
  };

  const instructionEl = document.getElementById('gallery-instruction');
  const stageEl = document.getElementById('gallery-stage');
  const counterEl = document.getElementById('gallery-counter');
  const prevBtn = document.getElementById('gallery-prev');
  const nextBtn = document.getElementById('gallery-next');
  const tabs = Array.from(document.querySelectorAll('#gallery-tabs .tab'));

  const filters = { room: 'all', nrel: 'all' };
  let method = 'ours';
  let index = 0;
  let list = [];

  function matches(entry) {
    return (filters.room === 'all' || entry.room === filters.room)
      && (filters.nrel === 'all' || String(entry.nrel) === filters.nrel);
  }

  function preload(entry) {
    if (entry) new Image().src = entry.img[method];
  }

  function renderScene() {
    const set = list[index];
    if (!set) {
      instructionEl.textContent = 'No scene matches this combination.';
      stageEl.replaceChildren();
      counterEl.textContent = '0 / 0';
      prevBtn.disabled = nextBtn.disabled = true;
      return;
    }
    instructionEl.textContent = '“' + set.text + '”';
    stageEl.replaceChildren(...METHODS.map(function (m) {
      const img = new Image();
      img.src = set.img[m];
      img.alt = LABELS[m] + ' result for the instruction: ' + set.text;
      img.dataset.method = m;
      if (m === method) img.className = 'is-active';
      return img;
    }));
    counterEl.textContent = (index + 1) + ' / ' + list.length;
    prevBtn.disabled = nextBtn.disabled = list.length < 2;
    preload(list[index + 1]);
    preload(list[index - 1]);
  }

  function setMethod(m) {
    method = m;
    tabs.forEach(function (t) { t.classList.toggle('is-active', t.dataset.method === m); });
    Array.from(stageEl.children).forEach(function (img) {
      img.classList.toggle('is-active', img.dataset.method === m);
    });
  }

  function step(delta) {
    if (!list.length) return;
    index = (index + delta + list.length) % list.length;
    renderScene();
  }

  function applyFilters() {
    list = QUALITATIVE.filter(matches);
    index = 0;
    renderScene();
  }

  document.querySelectorAll('.gallery-filters .filter-group').forEach(function (group) {
    const key = group.dataset.filter;
    group.addEventListener('click', function (e) {
      const chip = e.target.closest('.chip');
      if (!chip) return;
      filters[key] = chip.dataset.value;
      group.querySelectorAll('.chip').forEach(function (c) {
        c.classList.toggle('is-active', c === chip);
      });
      applyFilters();
    });
  });

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () { setMethod(tab.dataset.method); });
  });
  prevBtn.addEventListener('click', function () { step(-1); });
  nextBtn.addEventListener('click', function () { step(1); });

  document.addEventListener('keydown', function (e) {
    if (e.target.matches('input, textarea, select')) return;
    const seen = root.getBoundingClientRect();
    if (seen.bottom < 0 || seen.top > window.innerHeight) return;
    if (e.key === 'ArrowLeft') { step(-1); }
    else if (e.key === 'ArrowRight') { step(1); }
    else if (e.key >= '1' && e.key <= '4') { setMethod(METHODS[Number(e.key) - 1]); }
    else return;
    e.preventDefault();
  });

  applyFilters();
}());
