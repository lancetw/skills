// 塗鴉：ELI5 筆記自己帶的那張小圖。
//
// The model does not draw anything — it picks a name out of the vocabulary below and the page draws
// that. A model asked for raw SVG returns paths that fold in on themselves at 20px, and there is no
// way to check one before it is on the page; a name either matches a doodle here or is dropped.
//
// Drawn on a 40 grid at stroke 2, which is the smallest that survives the 22px margin size. Each
// shape is deliberately off — a leaf larger than its pair, a line that overshoots — so a row of them
// reads as pen marks in a notebook rather than a toolbar.
import { html } from './lib.js';

// `title` is lifted out of the props: SVG shows a tooltip from a <title> child, not from the
// attribute an HTML element would use, and a titled doodle is no longer purely decorative.
const doodle = children => ({ title, ...props }) => html`
  <svg className="doodle" viewBox="0 0 40 40" width="40" height="40" focusable="false"
       aria-hidden=${title ? undefined : 'true'} role=${title ? 'img' : undefined}
       fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" ...${props}>
    ${title ? html`<title>${title}</title>` : null}
    ${children}
  </svg>`;

// Keys are what the model writes. Names are English and concrete on purpose: 「經文」 or 「重要」 would
// have it choosing by topic, and every note would come back as the scroll.
// Null-prototype: a name arriving from a notes file rather than the schema must not be able to reach
// Object.prototype — DOODLES['constructor'] on a plain object hands React a function to render.
export const DOODLES = Object.assign(Object.create(null), {
  // 卷軸 — a text, a quotation, the wording itself
  scroll: doodle(html`
    <path d="M10 10c1-2.5 3.5-3.3 6-3h18c-2.5.8-3.6 2.5-3.2 4.5" />
    <path d="M10 10v18c.1 2.5-1 3.8-3.2 4.5h24c2.6-.7 3.6-2.2 3.2-4.6L28.6 11.5" />
    <path d="M15.5 16c3.8-.8 7.4.6 14-.3M15.5 21.5c3.2-.6 6.5.5 12-.2M15.5 27c2.6-.5 5-.3 8.5-.1" />`),
  // 燈 — light, seeing it, the point of the note
  lamp: doodle(html`
    <path d="M20 7.5c4.2.2 7.2 3.3 7 7.2-.1 2.4-1.4 4-2.4 5.7-.5.9-.6 1.7-.6 2.6h-8c0-.9-.2-1.7-.7-2.6-1-1.7-2.3-3.2-2.3-5.7 0-3.9 3-7.1 7-7.2Z" />
    <path d="M16.2 25.6h7.6M17.2 28.8h5.6" />
    <path d="M20 3.4V1.4M9.4 7.6 7.8 6M30.6 7.6 32.2 6M6 16.4H4M34 16.4h2" />`),
  // 放大鏡 — reading closer, a word worth stopping on
  lens: doodle(html`
    <path d="M5 11c4.4-.9 9 .6 14.4-.3M5 16.4c3.4-.7 7 .4 10.2-.1" />
    <circle cx="25.5" cy="22.5" r="7.6" />
    <path d="M31.2 28 36 33.4" />`),
  // 王冠 — a king, a throne, royal claims
  crown: doodle(html`
    <path d="M8.4 28.2 6.2 12.4l7 6.2 6.6-9.2 7 9.2 6.8-6.2-2.2 16Z" />
    <path d="M8.6 32.6c7.4-.9 15-.9 22.8 0" />`),
  // 水 — sea, river, flood
  water: doodle(html`
    <path d="M4 13c3.2-3.2 6-3.2 9.2 0s6 3.2 9.2 0 6-3.2 9.2 0" />
    <path d="M4 20.4c3.2-3.2 6-3.2 9.2 0s6 3.2 9.2 0 6-3.2 9.2 0" />
    <path d="M4 27.8c3.2-3.2 6-3.2 9.2 0s6 3.2 9.2 0 6-3.2 9.2 0" />`),
  // 火 — fire, judgement, the burning bush
  fire: doodle(html`
    <path d="M20 35c-5.6 0-9.4-3.6-9.4-8.4 0-5.2 3.8-7.9 5.2-12.9 2.7 2.5 3.3 4.8 3.1 7.3 2.1-2.5 2.7-5.6 2.1-9.4 5.2 3.5 8.4 9 8.4 15 0 4.8-3.8 8.4-9.4 8.4Z" />`),
  // 山 — a mountain, a height, Sinai or Zion
  mountain: doodle(html`
    <path d="M3.6 31.6 15 12.6l6.6 10.4 3.6-5.2L36.4 31.6Z" />
    <path d="M11.2 22.6c2.1 1.7 4.2 1.7 6.3 0" />`),
  // 路 — a journey, exile, coming and going
  path: doodle(html`
    <path d="M11 36c-1.6-8.6 7.2-10 7.2-16.2 0-4.4-5-4.8-5-9 0-2.8 2-4.6 5-5.4" />
    <path d="M23.4 36c-1.6-8.6 7.2-10 7.2-16.2 0-4.4-5-4.8-5-9 0-2.8 2-4.6 5-5.4" />`),
  // 門 — a gate, a threshold, entering
  door: doodle(html`
    <path d="M10 34.4V10c0-2 1.4-3.3 3.4-3.5h13.2c2 .2 3.4 1.5 3.4 3.5v24.4" />
    <path d="M8.4 34.6c8-.8 15.6-.8 23.2 0" />
    <circle cx="25" cy="21.4" r="1.3" />`),
  // 手 — an act, a gift, a hand stretched out
  hand: doodle(html`
    <path d="M13.6 34.2c-3-3-5.2-7.2-5.2-11.2 0-1.7 2.1-2.1 2.7-.4l1.5 3.2V9.4c0-2.5 3.1-2.5 3.1 0v9.7V7.2c0-2.5 3.3-2.5 3.3 0v11.9V8.8c0-2.5 3.1-2.5 3.1 0v10.9l.6-4.1c.4-2.3 3.3-1.7 2.9.6l-1.5 8.7c-.6 4.1-2.5 7.2-5.1 9.7Z" />`),
  // 星 — a sign, a promise, something marked out
  star: doodle(html`
    <path d="M20 5.2c1.6 8.6 3.7 12.5 8.6 14.1-4.9 1.6-7 5.5-8.6 14.1-1.6-8.6-3.7-12.5-8.6-14.1 4.9-1.6 7-5.5 8.6-14.1Z" />`),
  // 芽 — growth, a remnant, a new thing starting
  sprout: doodle(html`
    <path d="M20 35.4V20.2" />
    <path d="M20 24c-4.9.9-8.2-1.7-8.8-6.5 4.9-.9 8.2 1.7 8.8 6.5Z" />
    <path d="M20 27.6c4.7.3 8-2.5 7.8-6.8-4.7-.3-8 2.5-7.8 6.8Z" />`),
  // 問號 — the note is here because the obvious reading is wrong
  question: doodle(html`
    <path d="M13.4 14.6c-.2-4.2 2.8-7 6.8-7 3.8 0 6.6 2.4 6.6 5.8 0 4.6-6.2 5-6.2 9.8v1.8" />
    <path d="M20.5 32v.2" />`),
});

// The brand mark. Deliberately not in DOODLES: it is the one doodle that means the app rather than
// something a note says, and a model offered it would start picking it for verses about books.
export const Book = doodle(html`
  <path d="M20 12.4C16.8 9.4 12.4 8 6.6 8.2v20.4c5.8-.2 10.2 1.2 13.4 4.2 3.2-3 7.6-4.4 13.4-4.2V8.2c-5.8-.2-10.2 1.2-13.4 4.2Z" />
  <path d="M20 12.6v20.2" />
  <path d="M10.4 15.2c2.6-.3 4.9.1 6.9 1.2M10.4 21.4c2.6-.3 4.9.1 6.9 1.2" />
  <path d="M29.6 15.2c-2.6-.3-4.9.1-6.9 1.2M29.6 21.4c-2.6-.3-4.9.1-6.9 1.2" />`);

export const DOODLE_NAMES = Object.keys(DOODLES);

// One <svg> for a name, or nothing. An unknown name is not an error worth showing: the note is still
// a good note, it just doesn't get a picture.
export const Doodle = ({ name, ...props }) => {
  const D = DOODLES[name];
  return D ? html`<${D} ...${props} />` : null;
};
