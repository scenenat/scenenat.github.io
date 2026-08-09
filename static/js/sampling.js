/* Sampling-process viewer.
 *
 * Step 0 is the shared "everything is masked" grid and has no render to go with
 * it -- that is the honest state of the model at that point, so the render panel
 * shows the empty state instead of an image.
 */
(function () {
  const root = document.getElementById('sampling');
  if (!root || typeof SAMPLING === 'undefined' || !SAMPLING.length) return;

  const pickerEl = document.getElementById('sampling-scenes');
  const maskEl = document.getElementById('sampling-mask');
  const renderEl = document.getElementById('sampling-render');
  const emptyEl = renderEl.querySelector('.empty-state');
  const slider = document.getElementById('sampling-slider');
  const readout = document.getElementById('sampling-step');
  const playBtn = document.getElementById('sampling-play');

  const PLAY_MS = 750;
  let sceneIndex = 0;
  let stepIndex = 0;
  let timer = null;

  function scene() { return SAMPLING[sceneIndex]; }

  function buildScene() {
    const s = scene();
    slider.max = String(s.steps.length - 1);
    maskEl.replaceChildren(...s.steps.map(function (step) {
      const img = new Image();
      img.src = s.mask[String(step)];
      img.alt = 'Mask state at step ' + step;
      img.dataset.step = String(step);
      return img;
    }));
    renderEl.replaceChildren(emptyEl, ...s.steps.filter(function (step) {
      return s.render[String(step)];
    }).map(function (step) {
      const img = new Image();
      img.src = s.render[String(step)];
      img.alt = 'Scene decoded after ' + step + ' steps';
      img.dataset.step = String(step);
      return img;
    }));
    showStep();
  }

  function showStep() {
    const s = scene();
    const step = s.steps[stepIndex];
    [maskEl, renderEl].forEach(function (stage) {
      Array.from(stage.querySelectorAll('img')).forEach(function (img) {
        img.classList.toggle('is-active', img.dataset.step === String(step));
      });
    });
    emptyEl.hidden = Boolean(s.render[String(step)]);
    readout.textContent = 'step ' + step;
    slider.value = String(stepIndex);
  }

  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
    playBtn.innerHTML = '&#9654;';
    playBtn.setAttribute('aria-label', 'Play the sampling process');
  }

  function play() {
    timer = setInterval(function () {
      stepIndex = (stepIndex + 1) % scene().steps.length;
      showStep();
    }, PLAY_MS);
    playBtn.innerHTML = '&#9646;&#9646;';
    playBtn.setAttribute('aria-label', 'Pause the sampling process');
  }

  pickerEl.replaceChildren(...SAMPLING.map(function (s, i) {
    const btn = document.createElement('button');
    btn.className = 'chip' + (i === 0 ? ' is-active' : '');
    btn.textContent = s.label;
    btn.addEventListener('click', function () {
      sceneIndex = i;
      stepIndex = 0;
      pickerEl.querySelectorAll('.chip').forEach(function (c) {
        c.classList.toggle('is-active', c === btn);
      });
      buildScene();
    });
    return btn;
  }));

  slider.addEventListener('input', function () {
    stop();
    stepIndex = Number(slider.value);
    showStep();
  });

  playBtn.addEventListener('click', function () { timer ? stop() : play(); });

  buildScene();
}());
