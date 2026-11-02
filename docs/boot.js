/* Start-up: dashboard tabs and summary report modal. */
(function () {
  'use strict';
  const { D, L, esc, $ } = APP;

  // ---- minimal Markdown -> HTML for the summary report
  const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\*(.+?)\*/g, '<i>$1</i>').replace(/`(.+?)`/g, '<code>$1</code>');
  function md(src) {
    const out = [], lines = src.split('\n'); let i = 0;
    while (i < lines.length) {
      const l = lines[i];
      if (/^#{1,3} /.test(l)) { const n = l.match(/^#+/)[0].length; out.push(`<h${n}>${inline(l.replace(/^#+ /, ''))}</h${n}>`); i++; }
      else if (/^\|/.test(l) && /^\|[-| ]+\|$/.test(lines[i + 1] || '')) {
        const cells = (r) => r.replace(/^\||\|$/g, '').split('|').map((c) => c.trim()); const head = cells(l); i += 2; const rows = [];
        while (i < lines.length && /^\|/.test(lines[i])) rows.push(cells(lines[i++]));
        out.push(`<div class="tbl-wrap"><table><thead><tr>${head.map((h) => `<th>${inline(h)}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`);
      } else if (/^\s*[-*] /.test(l)) { const items = []; while (i < lines.length && /^\s*[-*] /.test(lines[i])) items.push(lines[i++].replace(/^\s*[-*] /, '')); out.push(`<ul>${items.map((t) => `<li>${inline(t)}</li>`).join('')}</ul>`); }
      else if (l.trim() === '') i++;
      else { out.push(`<p>${inline(l)}</p>`); i++; }
    }
    return out.join('');
  }
  function showSummary() {
    APP.modal(`<div class="row-tools"><button class="btn-ghost" id="dlMd">⬇ ดาวน์โหลดรายงาน (.md)</button></div><div class="md">${md(D.summary_md || '# ไม่มีรายงาน')}</div>`);
    $('#dlMd').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([D.summary_md], { type: 'text/markdown;charset=utf-8' })); a.download = 'dashboard_summary.md'; a.click(); };
  }
  APP.mdToHtml = md;

  // ---- wiring
  $('#btnSummary').addEventListener('click', showSummary);
  $('#loading').hidden = true; APP.buildSidebar(); APP.buildTabs(); APP.refresh();
})();
