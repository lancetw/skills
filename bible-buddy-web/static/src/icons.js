// One 16×16 stroke icon set, drawn inline so nothing is fetched and every glyph inherits the
// surrounding text colour. Emoji were doing this job before; they render as a different typeface
// on every machine, ignore the theme, and can't be sized against the label beside them.
import { html } from './lib.js';

// 1.5 stroke on a 16 grid reads at the same weight as the UI text at .8–.85rem
const svg = (children, { fill = false, box = 16 } = {}) => props => html`
  <svg className="icon" viewBox=${`0 0 ${box} ${box}`} width="16" height="16" aria-hidden="true" focusable="false"
       fill=${fill ? 'currentColor' : 'none'} stroke=${fill ? 'none' : 'currentColor'}
       strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" ...${props}>
    ${children}
  </svg>`;

export const Search = svg(html`
  <circle cx="7" cy="7" r="4.25" />
  <path d="M10.3 10.3 13.5 13.5" />`);

// 對照 = one page split in two columns, which is what the toggle actually does
export const Columns = svg(html`
  <rect x="2.25" y="3" width="11.5" height="10" rx="1.5" />
  <path d="M8 3v10" />`);

export const Moon = svg(html`<path d="M13.2 9.6A5.6 5.6 0 1 1 6.4 2.8a4.4 4.4 0 0 0 6.8 6.8Z" />`);

export const Sun = svg(html`
  <circle cx="8" cy="8" r="3" />
  <path d="M8 1.5v1.4M8 13.1v1.4M2.4 2.4l1 1M12.6 12.6l1 1M1.5 8h1.4M13.1 8h1.4M2.4 13.6l1-1M12.6 3.4l1-1" />`);

export const Chat = svg(html`
  <path d="M14 10.2a1.6 1.6 0 0 1-1.6 1.6H6.2L3 14.2V4.4A1.6 1.6 0 0 1 4.6 2.8h7.8A1.6 1.6 0 0 1 14 4.4Z" />`);

// the ELI5 pass: a four-point sparkle. Drawn on a 24 grid because the concave curves need the
// room — the same shape plotted straight onto 16 collapses into a plus sign at button size.
export const Sparkle = svg(html`
  <path d="M11.5 2.4a.5.5 0 0 1 1 0l1.1 4.3a4 4 0 0 0 2.7 2.7l4.3 1.1a.5.5 0 0 1 0 1l-4.3 1.1a4 4 0 0 0-2.7 2.7l-1.1 4.3a.5.5 0 0 1-1 0l-1.1-4.3a4 4 0 0 0-2.7-2.7l-4.3-1.1a.5.5 0 0 1 0-1l4.3-1.1a4 4 0 0 0 2.7-2.7Z" />`,
  { fill: true, box: 24 });

export const Trash = svg(html`
  <path d="M2.8 4.4h10.4M6.4 4.4V2.8h3.2v1.6" />
  <path d="M4.4 4.4l.5 8.1a1 1 0 0 0 1 .9h4.2a1 1 0 0 0 1-.9l.5-8.1" />`);

export const Refresh = svg(html`
  <path d="M13.4 8a5.4 5.4 0 1 1-1.7-3.9" />
  <path d="M13.6 1.9v3.4h-3.4" />`);

// 驗證 = a check that has been stamped, not a magnifier: the agent signs the note off
export const BadgeCheck = svg(html`
  <circle cx="8" cy="8" r="5.6" />
  <path d="M5.6 8.1 7.3 9.8l3.2-3.6" />`);

export const ArrowRight = svg(html`<path d="M2.8 8h9.4M8.6 4.4 12.2 8l-3.6 3.6" />`);

export const Pencil = svg(html`
  <path d="M11.1 2.7a1.7 1.7 0 0 1 2.4 2.4L5.4 13.2 2.3 13.9l.7-3.1Z" />`);

export const Check = svg(html`<path d="M3.2 8.4 6.3 11.5 12.8 4.5" />`);

export const Close = svg(html`<path d="M4 4l8 8M12 4l-8 8" />`);

// the one "something went wrong" mark: a circle with a bang, never a red ✗ glyph
export const Alert = svg(html`
  <circle cx="8" cy="8" r="5.6" />
  <path d="M8 5.1v3.5" />
  <path d="M8 10.7v.05" />`);

// back to the verse a footnote came from
export const Back = svg(html`<path d="M12.4 3v4.6a1.6 1.6 0 0 1-1.6 1.6H3.9M6.4 11.7 3.7 9.2l2.7-2.5" />`);

export const Stop = svg(html`<rect x="4.2" y="4.2" width="7.6" height="7.6" rx="1.2" />`);
