// The rules for changing the list of notes on screen. No imports, so they are testable without a
// browser — they used to be written out seven times, in two files, with different answers to the
// same question (does a note already on screen get overwritten by a cached pass? does a rewrite
// keep its position?). Every one returns a new list, because React only re-renders if it does.

// The note the server just sent us, whether or not we already had it. Order is kept: a note that
// moved to the end would drag its arrow across the verse.
export const upsert = (list, n) =>
  (list.some(x => x.id === n.id) ? list.map(x => (x.id === n.id ? n : x)) : [...list, n]);

// An automatic pass offering its whole set. What is already on screen wins — the pass is cached and
// re-offers the same notes on every load, and one of them may have been edited since.
export const mergeNew = (list, incoming) =>
  [...list, ...incoming.filter(n => !list.some(x => x.id === n.id))];

// A rewrite lands where the old note was. Without an id to replace, it is just a new note.
export const replaceOrAdd = (list, id, n) =>
  (id ? list.map(x => (x.id === id ? n : x)) : upsert(list, n));

export const without = (list, id) => list.filter(x => x.id !== id);

// 🗑 clears every automatic note (ELI5, agent, references) and spares the reader's own.
export const onlyMine = list => list.filter(x => x.author === 'user');
