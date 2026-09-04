// Every change to the list of notes on screen: the rule, the request that earns it, and what happens
// when the request fails. The rules used to live alone in notelist.js and were tested alone, while
// the verb and the failure policy stayed at six call sites in two files — which is where the bug was:
// 刪除 threw the server's answer away and dropped the note regardless, so a failed delete vanished
// from the screen and came back on the next load, while the same operation one level up (🗑) checked.
// A rule now only runs once the server has agreed, and it runs in one place.
//
// No imports: `api` comes in at construction, so `node --test` drives the whole thing.

// ── the rules ─────────────────────────────────────────────────────────────────
// Private: a caller reaches one only through the verb that earns it. Every one returns a new list,
// because React re-renders only if it does, and order is kept everywhere — a note that moved to the
// end would drag its arrow across the verse.

const upsert = (list, n) =>
  (list.some(x => x.id === n.id) ? list.map(x => (x.id === n.id ? n : x)) : [...list, n]);

// An automatic pass offering its whole set. What is already on screen wins: the pass is cached and
// re-offers the same notes on every load, and one of them may have been edited since.
const mergeNew = (list, incoming) =>
  [...list, ...incoming.filter(n => !list.some(x => x.id === n.id))];

// A rewrite lands where the old note was. Without an id to replace, it is just a new note.
const replaceOrAdd = (list, id, n) => (id ? list.map(x => (x.id === id ? n : x)) : upsert(list, n));

const without = (list, id) => list.filter(x => x.id !== id);

const onlyMine = list => list.filter(x => x.author === 'user');

// ── the verbs ─────────────────────────────────────────────────────────────────
// `apply` is the page's state setter, called with an updater and only once the server has agreed.
// Every verb answers `{ error }` or its result and never throws, because `api` never rejects either.

export function makeNotes({ api, apply }) {
  return {
    // The passage changed: whatever the server holds for it is the list now. A failure still clears,
    // because the previous passage's notes must not stay on screen beside the new verses.
    async refresh() {
      const fresh = await api('/api/notes');
      const ok = Array.isArray(fresh);
      apply(() => (ok ? fresh : []));
      return ok ? { count: fresh.length } : { error: fresh?.error || '伺服器回傳異常' };
    },

    // An automatic pass — the reference tables on load, or the ELI5 sweep behind the button.
    async applyPass(url) {
      const r = await api(url);
      const incoming = Array.isArray(r) ? r : r?.notes;   // the quick pass wraps its list; refs does not
      if (!Array.isArray(incoming)) return { error: r?.error || '伺服器回傳異常' };
      apply(cur => mergeNew(cur, incoming));
      return { added: incoming.length, cached: !!r.cached, cost: r.cost };
    },

    // A note the agent pushed down the event stream. Already on disk server-side; nothing to ask.
    applyServer(note) {
      apply(cur => upsert(cur, note));
    },

    // The model's note for one selection. `replaceId` is set when it was a rewrite of an old one.
    applyOne(note, replaceId) {
      apply(cur => replaceOrAdd(cur, replaceId, note));
    },

    // Create (no id) or edit (id). What lands is the note the server hands back, not the patch.
    async save(note, patch) {
      const saved = note.id
        ? await api('/api/notes/' + note.id, 'PUT', patch)
        : await api('/api/notes', 'POST', { ...note, ...patch });
      if (saved?.error || !saved?.id) return { error: saved?.error || '伺服器回傳異常' };
      apply(cur => replaceOrAdd(cur, note.id, saved));
      return { note: saved };
    },

    // The note leaves the screen only if the server was reached. An `ok: false` means it had already
    // gone, so it leaves too — only a request that never landed keeps it, because it is still there.
    async remove(id) {
      const r = await api('/api/notes/' + id, 'DELETE');
      if (r?.error) return { error: r.error };
      apply(cur => without(cur, id));
      return { ok: true };
    },

    // 🗑 every automatic note of the passage (ELI5, agent, references); the reader's own stay.
    async clearAuto() {
      const r = await api('/api/notes/quick', 'DELETE');
      if (r?.error) return { error: r.error };
      apply(onlyMine);
      return { removed: r?.removed ?? 0 };
    },
  };
}
