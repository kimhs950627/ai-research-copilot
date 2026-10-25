/* paginate.js — fill fixed-height cue cards from the flat block list in #src.
 *
 * Filling rules:
 *   - a part (#) or section (##) opens a new card and can never share a card;
 *   - a section that does not fit one card is spread over the smallest number of cards
 *     it needs, near-equally, so no card ends up holding a single stranded line;
 *   - blocks are never split and never shrunk. Heights come from measuring the real
 *     rendered block in an off-canvas scratch card, and the final placement of every
 *     block is still checked with getBoundingClientRect() so nothing can be clipped.
 *
 * Runs synchronously on DOMContentLoaded (system fonts are already available), again when
 * document.fonts.ready resolves, and once more before printing.
 */
(function () {
  var src = document.getElementById('src');
  var deck = document.getElementById('deck');
  if (!src || !deck) return;

  var RAW = src.innerHTML;
  var per = document.body.classList.contains('per4') ? 4 : 2;
  var title = document.body.dataset.title || '';
  var state, cards, cur, scratch, scratchBody, overfull;

  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function newSheet() {
    var sheet = el('div', 'sheet');
    for (var i = 0; i < per; i++) {
      var card = el('div', 'card');
      card.dataset.slot = String(i + 1);
      var top = el('div', 'ctop');
      top.appendChild(el('span', 'crun'));
      top.appendChild(el('span', 'ccnt'));
      card.appendChild(top);
      card.appendChild(el('div', 'cttl'));
      card.appendChild(el('div', 'cbody'));
      var foot = el('div', 'cfoot');
      foot.appendChild(el('span', 'cfl'));
      foot.appendChild(el('span', 'cfr'));
      card.appendChild(foot);
      sheet.appendChild(card);
    }
    sheet.appendChild(el('div', 'cut-h'));
    if (per === 4) sheet.appendChild(el('div', 'cut-v'));
    deck.appendChild(sheet);
    return sheet;
  }

  function nextSlot() {
    var sheet = deck.lastElementChild;
    var used = sheet ? Number(sheet.dataset.used || 0) : per;
    if (!sheet || used >= per || used < 0) {
      sheet = newSheet();
      used = 0;
    }
    var slots = sheet.querySelectorAll('.card');
    if (used >= slots.length) {
      reportInto({ slotbug: 'used=' + used + ' slots=' + slots.length + ' sheets=' +
        deck.querySelectorAll('.sheet').length + ' cards=' + cards.length });
      sheet = newSheet();
      used = 0;
      slots = sheet.querySelectorAll('.card');
    }
    sheet.dataset.used = String(used + 1);
    return slots[used];
  }

  function addCard(cont) {
    var card = nextSlot();
    card.querySelector('.crun').textContent = title;
    var head = card.querySelector('.cttl');
    head.textContent = '';
    if (state.num) head.appendChild(el('span', 'snum', '§' + state.num));
    head.appendChild(el('span', 'stitle', state.title || state.part || title));
    if (state.time) head.appendChild(el('span', 'ctime', state.time));
    if (cont) {
      card.classList.add('cont');
      head.appendChild(el('span', 'cmark', '계속'));
    }
    if (!state.num && !state.title) card.classList.add('part-only');
    card.dataset.part = state.part;
    cards.push(card);
    return card;
  }

  function ensureCard() {
    if (!cur) cur = addCard(false);
    return cur;
  }

  function box(card) { return card.querySelector('.cbody'); }

  /* Painted extent, not scrollHeight: a trailing bottom margin is not clipping, and
     counting it would push a block to the next card for nothing. */
  function overflows(node) {
    var last = node.lastElementChild;
    if (!last) return false;
    return last.getBoundingClientRect().bottom > node.getBoundingClientRect().bottom;
  }

  function setupScratch() {
    scratch = el('div', 'scratch');
    var card = el('div', 'card');
    card.appendChild(el('div', 'ctop'));
    card.appendChild(el('div', 'cttl'));
    scratchBody = el('div', 'cbody');
    card.appendChild(scratchBody);
    scratch.appendChild(card);
    document.body.appendChild(scratch);
  }

  /* Append each node in turn to an unlimited-height copy of a card body and record how
     much the body grew, which is the exact space the block will occupy in a card. */
  function measure(nodes) {
    scratchBody.textContent = '';
    var heights = [];
    var before = scratchBody.getBoundingClientRect().height;
    for (var i = 0; i < nodes.length; i++) {
      scratchBody.appendChild(nodes[i]);
      var now = scratchBody.getBoundingClientRect().height;
      heights.push(now - before);
      before = now;
    }
    scratchBody.textContent = '';
    return heights;
  }

  /* Fill the cards for one run of blocks (the body of a section, or the front matter). */
  function placeRun(run) {
    var first = ensureCard();
    if (!run.length) return;

    var heights = measure(run);
    var total = 0;
    for (var i = 0; i < heights.length; i++) total += heights[i];

    var spaces = [Math.max(box(first).clientHeight, 1)];
    var created = [first];
    if (total > spaces[0]) {
      /* the second card is always used when the first one overflows, and its shorter
         continuation header is exactly what gives every later card its extra room */
      var second = addCard(true);
      created.push(second);
      spaces.push(Math.max(box(second).clientHeight, 1));
    }
    while (spaces.length > 1 && spaces.length < 1 + Math.ceil(
             Math.max(0, total - spaces[0]) / spaces[1])) {
      spaces.push(spaces[1]);
    }

    var index = 0;
    var remaining = total;
    for (var c = 0; index < run.length; c++) {
      var card = created[c];
      if (!card) {
        card = addCard(true);
        created[c] = card;
        spaces[c] = spaces[1] || spaces[0];
      }
      var target = box(card);
      var space = spaces[c];
      var planned = spaces.length - c; /* cards the plan still expects */
      var share = planned > 0 ? remaining / planned : remaining;
      var rest = 0;
      for (var later = c + 1; later < spaces.length; later++) rest += spaces[later];
      var lastPlanned = c === spaces.length - 1;

      /* Break where this card is closest to its fair share of the remaining height, without
         passing the card's own space and without leaving more than the later cards hold.
         With no such break, take everything this card holds and carry on to a new card. */
      var cum = 0;
      var stop = index;
      var bestGap = Infinity;
      var maxFit = index;
      for (var j = index; j < run.length; j++) {
        if (cum + heights[j] > space) break;
        cum += heights[j];
        maxFit = j + 1;
        if (!lastPlanned && remaining - cum > rest) continue;
        var gap = Math.abs(cum - share);
        if (gap < bestGap) { bestGap = gap; stop = j + 1; }
      }
      if (stop === index) stop = Math.max(maxFit, index + 1);

      var used = 0;
      while (index < stop) {
        target.appendChild(run[index]);
        if (overflows(target)) {
          if (used === 0) { overfull++; card.classList.add('overfull'); }
          else { target.removeChild(run[index]); break; }
        }
        used += heights[index];
        index++;
      }
      remaining -= used;
    }

    while (index < run.length) { /* a block taller than a whole card: one card each */
      var spill = box(addCard(true));
      spill.appendChild(run[index++]);
      overfull++;
      spill.parentElement.classList.add('overfull');
    }
  }

  function collect(blocks, from) {
    var items = [];
    var i = from;
    while (i < blocks.length) {
      var kind = blocks[i].dataset.kind;
      if (kind === 'part' || kind === 'section' || kind === 'rule') break;
      items.push(blocks[i]);
      i++;
    }
    return { items: items, next: i };
  }

  function paginate() {
    src.innerHTML = RAW; /* a previous pass moved the blocks into cards */
    var blocks = Array.prototype.slice.call(src.children);
    deck.textContent = '';
    if (!scratch) setupScratch();
    cards = [];
    cur = null;
    overfull = 0;
    state = { part: '', num: '', title: '', time: '' };

    var i = 0;
    while (i < blocks.length) {
      var block = blocks[i];
      var kind = block.dataset.kind;

      if (kind === 'part') {
        state = { part: block.dataset.title || '', num: '', title: '', time: '' };
        i++;
      } else if (kind === 'section') {
        state.num = block.dataset.num || '';
        state.title = block.dataset.title || '';
        state.time = block.dataset.time || '';
        i++;
      } else if (kind === 'rule') {
        i++;
      } else {
        var run = collect(blocks, i);
        i = run.next;
        placeRun(run.items);
        cur = cards.length ? cards[cards.length - 1] : null;
        continue;
      }
      /* a part/section/rule starts a fresh card; only a run with content makes one */
      cur = null;
      var after = collect(blocks, i);
      if (after.items.length) {
        i = after.next;
        placeRun(after.items);
        cur = cards.length ? cards[cards.length - 1] : null;
      }
    }

    for (var k = 0; k < cards.length; k++) {
      var label = pad(k + 1) + ' / ' + pad(cards.length);
      cards[k].querySelector('.ccnt').textContent = '카드 ' + label;
      cards[k].querySelector('.cfr').textContent = label;
      var part = cards[k].dataset.part || '';
      if (part.length > 30) part = part.slice(0, 29) + '…'; /* long part titles stay a footer */
      cards[k].querySelector('.cfl').textContent = part;
    }

    var last = deck.lastElementChild;
    if (last) { /* hide the hairlines of an unused slot in the final sheet */
      var slots = last.querySelectorAll('.card');
      for (var s = Number(last.dataset.used || 0); s < slots.length; s++) slots[s].classList.add('blank');
    }

    reportInto({
      cards: String(cards.length),
      sheets: String(deck.querySelectorAll('.sheet').length),
      overfull: String(overfull),
      titles: cards.map(function (card) {
        var num = card.querySelector('.snum');
        var name = card.querySelector('.stitle');
        return (num ? num.textContent : '') + (name ? name.textContent : '') +
          (card.classList.contains('cont') ? '+' : '');
      }).join(' | '),
      fill: cards.map(function (card) {
        var container = box(card);
        var lastNode = container.lastElementChild;
        if (!lastNode) return 0;
        var outer = container.getBoundingClientRect();
        var inner = lastNode.getBoundingClientRect();
        return outer.height ? Math.round(100 * (inner.bottom - outer.top) / outer.height) : 0;
      }).join(',')
    });
  }

  function reportInto(values) {
    var report = document.getElementById('report');
    if (!report) {
      report = el('div');
      report.id = 'report';
      document.body.appendChild(report);
    }
    for (var key in values) report.dataset[key] = values[key];
    return report;
  }

  /* A broken paginator must fail loudly: the report carries the error and the PDF then
     fails the generator's own block-fidelity check instead of printing half the script. */
  function safePaginate() {
    try {
      paginate();
    } catch (error) {
      reportInto({ error: String((error && error.message) || error) + ' @ ' + String((error && error.stack) || '').split('\n').slice(0, 3).join(' | ') });
    }
  }

  safePaginate();
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () {
      safePaginate();
      /* one settle pass: a font fallback can grow a line box after fonts.ready resolves */
      setTimeout(safePaginate, 400);
    });
  }
  window.addEventListener('beforeprint', safePaginate);
})();
