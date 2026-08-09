/* Room-type toggle on the main result table, and the in-the-wild tab strip. */
(function () {
  const toggle = document.getElementById('main-table-toggle');
  if (toggle) {
    const bodies = Array.from(document.querySelectorAll('.result-table tbody[data-room]'));
    toggle.addEventListener('click', function (e) {
      const chip = e.target.closest('.chip');
      if (!chip) return;
      toggle.querySelectorAll('.chip').forEach(function (c) {
        c.classList.toggle('is-active', c === chip);
      });
      bodies.forEach(function (b) { b.hidden = b.dataset.room !== chip.dataset.room; });
    });
  }
}());

(function () {
  const tabsEl = document.getElementById('wild-tabs');
  const bodyEl = document.getElementById('wild-body');
  if (!tabsEl || !bodyEl || typeof WILD === 'undefined') return;

  // The paper is explicit that negation is the one instruction type SceneNAT does
  // not reliably honour, so that group says so rather than being quietly dropped.
  const NOTES = {
    negative: 'Negation is the weak spot. Positive examples dominate training, so the '
      + 'model often places the object it was told to leave out.',
    arbitration: 'When an instruction is physically impossible, SceneNAT keeps the layout '
      + 'plausible rather than forcing the relation.',
    llm: 'These prompts are rewritten into explicit relations by a general-purpose LLM '
      + 'first; SceneNAT itself is unchanged.',
  };

  function show(group) {
    const parts = [];
    if (NOTES[group.key]) {
      parts.push('<p class="wild-note">' + NOTES[group.key] + '</p>');
    }
    parts.push('<div class="wild-grid">' + group.examples.map(function (ex) {
      return '<figure class="wild-card"><img src="' + ex.img + '" alt="Scene generated for: '
        + ex.text.replace(/"/g, '&quot;') + '" loading="lazy"><p>“' + ex.text + '”</p></figure>';
    }).join('') + '</div>');
    bodyEl.innerHTML = parts.join('');
  }

  WILD.filter(function (g) { return g.examples.length; }).forEach(function (group, i) {
    const btn = document.createElement('button');
    btn.className = 'chip' + (i === 0 ? ' is-active' : '');
    btn.textContent = group.label;
    btn.addEventListener('click', function () {
      tabsEl.querySelectorAll('.chip').forEach(function (c) {
        c.classList.toggle('is-active', c === btn);
      });
      show(group);
    });
    tabsEl.appendChild(btn);
    if (i === 0) show(group);
  });
}());
