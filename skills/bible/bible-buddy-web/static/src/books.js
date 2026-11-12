// The 66 books in canon order with their chapter counts, for the 目錄 menu. No import, so the
// table is testable without a browser. Names are bible-buddy's own Chinese names (book_names.py),
// which is what /api/passage resolves; bible-buddy keeps no chapter counts, so they live here.
export const BOOKS = [
  ['創世記', 50], ['出埃及記', 40], ['利未記', 27], ['民數記', 36], ['申命記', 34],
  ['約書亞記', 24], ['士師記', 21], ['路得記', 4], ['撒母耳記上', 31], ['撒母耳記下', 24],
  ['列王紀上', 22], ['列王紀下', 25], ['歷代志上', 29], ['歷代志下', 36], ['以斯拉記', 10],
  ['尼希米記', 13], ['以斯帖記', 10], ['約伯記', 42], ['詩篇', 150], ['箴言', 31],
  ['傳道書', 12], ['雅歌', 8], ['以賽亞書', 66], ['耶利米書', 52], ['耶利米哀歌', 5],
  ['以西結書', 48], ['但以理書', 12], ['何西阿書', 14], ['約珥書', 3], ['阿摩司書', 9],
  ['俄巴底亞書', 1], ['約拿書', 4], ['彌迦書', 7], ['那鴻書', 3], ['哈巴谷書', 3],
  ['西番雅書', 3], ['哈該書', 2], ['撒迦利亞書', 14], ['瑪拉基書', 4],
  ['馬太福音', 28], ['馬可福音', 16], ['路加福音', 24], ['約翰福音', 21], ['使徒行傳', 28],
  ['羅馬書', 16], ['哥林多前書', 16], ['哥林多後書', 13], ['加拉太書', 6], ['以弗所書', 6],
  ['腓立比書', 4], ['歌羅西書', 4], ['帖撒羅尼迦前書', 5], ['帖撒羅尼迦後書', 3], ['提摩太前書', 6],
  ['提摩太後書', 4], ['提多書', 3], ['腓利門書', 1], ['希伯來書', 13], ['雅各書', 5],
  ['彼得前書', 5], ['彼得後書', 3], ['約翰一書', 5], ['約翰二書', 1], ['約翰三書', 1],
  ['猶大書', 1], ['啟示錄', 22],
];

export const OT = BOOKS.slice(0, 39), NT = BOOKS.slice(39);

// The book a typed reference names, as the table spells it, or null. Exact first, then the same
// partial match the server's lookup() accepts (「約翰」 is 約翰福音), so the menu opens on the book
// the page is showing even when the box holds a short form.
export function findBook(name) {
  const s = (name || '').trim();
  if (!s) return null;
  return BOOKS.find(([n]) => n === s)?.[0] ?? BOOKS.find(([n]) => n.includes(s) || s.includes(n))?.[0] ?? null;
}
