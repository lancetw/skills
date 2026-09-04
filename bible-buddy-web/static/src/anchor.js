// Where a reader's selection sits in the verse text. No imports, so the mapping is testable without
// a browser — it used to be `v.text.indexOf(quote)`, which anchors every repeated phrase to its
// first occurrence: drag the second 「神」 of a verse and the note landed on the first.
//
// A verse element holds more than verse text (the verse number, the 原 button, the doodle stack,
// footnote markers, the chip row). The caller walks the element and passes only the text nodes that
// carry verse text, in document order; the offsets below are offsets into `v.text`.

export function offsetOf(nodes, node, offset) {
  let n = 0;
  for (const t of nodes) {
    if (t === node) return n + offset;
    n += t.data.length;
  }
  return -1;   // the selection started somewhere that is not verse text
}

// Trim a [start, end) span down to its non-blank text. A double-click or a drag past the end of a
// line hands us the surrounding whitespace, and a quote must be the words the reader meant.
export function trimSpan(text, start, end) {
  while (start < end && /\s/.test(text[start])) start++;
  while (end > start && /\s/.test(text[end - 1])) end--;
  return [start, end];
}
