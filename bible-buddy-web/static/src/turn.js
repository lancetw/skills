// One agent turn, read off its SSE stream. No imports: the page's only job here is to say what to do
// with each event, and a test can hand this a fake response with no browser in the room.
//
// The contract is the reason this is its own module: `on.end` runs exactly once, on every path out —
// a done event, an error event, the stream stopping early, a frame that will not parse, a dead
// socket, or a handler of yours that throws. A turn that never reports its end leaves the composer
// disabled with a refresh as the only way back, which is what used to happen.
//
// reason: 'done' | 'error' | 'closed' (stream stopped before the turn said so) | 'failed' (it threw)

export async function readTurn(res, on = {}) {
  let reason = null, err = null;
  try {
    const rd = res.body.getReader(), dec = new TextDecoder();
    let rest = '';
    for (;;) {
      const { value, done } = await rd.read();
      if (done) break;
      rest += dec.decode(value, { stream: true });
      let i;
      while ((i = rest.indexOf('\n\n')) >= 0) {
        const line = rest.slice(0, i); rest = rest.slice(i + 2);
        if (!line.startsWith('data: ')) continue;   // ": keepalive" and blank frames
        let ev;
        try { ev = JSON.parse(line.slice(6)); } catch { continue; }  // an unreadable frame is not worth losing the turn over
        if (ev.type === 'done' || ev.type === 'error') reason = ev.type;  // set before the handler runs, so a throwing handler still reports the truth
        on[ev.type]?.(ev);
      }
    }
  } catch (e) {
    reason = 'failed';
    err = e;
  } finally {
    on.end?.(reason || 'closed', err);
  }
  return reason || 'closed';
}
