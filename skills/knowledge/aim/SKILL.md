---
name: aim
description: Rewrite a task prompt so a model aims higher instead of only faster — up in altitude (the goal beyond the goal), down in depth (an expert's instruments, the raw data, an outside judge) and out in range (fields the task never names) — and hand back the rewritten prompt without running it. Use when the user asks to make a prompt, task or plan more ambitious, deeper or less shallow, says "we're not ambitious enough", 「更有野心」「想大一點」「做深一點」「幫我把這個 prompt 升級」, or hands over a routine task (fill a template, fix one bug, make a deck) and asks how to get more out of the model.
license: MIT
---

# Aim

Speed (the same work in less time) needs no help. This skill works the other three kinds of ambition:

- **Altitude** — aim at the outcome, not the task.
- **Depth** — do the task the way the best person in the field would.
- **Range** — bring in fields the task does not name.

Adapted from Felix Rieseberg, "How to be more ambitious: A tutorial for humans with models": <https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/>

**The rewritten prompt is the deliverable. Do not run it**: running it is a new request the user makes after reading it.

## Workflow

1. **Read** — name the deliverable, the material it starts from, and the field whose judgement the result rests on: a named profession ("SRE", "forensic accountant"), never "an expert". Glance at the workspace to name real sources (log directory, test suite, raw export, connected MCP data); the task itself waits.
   Done when: deliverable, starting material and field are each one concrete noun phrase.

2. **Altitude** — ask what should happen *after* the deliverable: the goal beyond the goal. Climb one rung at a time, e.g. for a quarterly review deck:
   fill the template → explain what changed, why, and which decisions it forces (with for/against arguments) → replace the process with something that catches the same problems sooner, tested against our own history and run beside the old one for a cycle.
   Stop at the highest rung that has an outside judge and the access to own it, and name that access (crash reports, a version → commit mapping, machines to reproduce on). The tell that altitude fits: people will hold meetings about this work. Creative or one-off work stays at task level; say so in one line.
   Done when: a rung is chosen and its required access is named, or "n/a because …".

3. **Depth** — answer four questions for this prompt:
   - (a) the move a top practitioner makes that the prompt leaves out;
   - (b) the rawest material, written "instead of X → Y" with where Y lives. Turn a belief into a test: "we think churn is an onboarding problem; try to reproduce that from the raw data";
   - (c) the instruments the best in the field use: a database and a statistical model, not a markdown table. Models asked to act like a professional switch vocabulary without switching methods; name the method;
   - (d) the outside judge (a test, a benchmark, held-out data, a reproduction) and its pass threshold. Never the model judging itself.
   Set the numeric target at a demanding bar and state it as reachable (5 s → 200 ms). Where the material allows, ask for new knowledge, not just a check: "find the earliest churn signal we don't know yet and show it predicts on data it has not seen". The user's hard limits (budget, deadline, audience) hold.
   Done when: (a)–(d) each have a concrete answer.

4. **Range** — restate the deliverable's noun as verbs: "a QBR deck" → "get busy people to believe a cause-and-effect story and decide under uncertainty in 30 minutes". Pick 1–3 fields those verbs call for, at least one adversarial (short seller, forensic accountant, hostile reviewer), each paired with the technique it performs. Ask for what a short seller *does* to research a position, never for writing *like* one: role play makes the transcript weirder without making the result better. A field with no technique is decoration; drop it.
   Done when: each field has a named technique, and one field is adversarial or "n/a because …".

5. **Rewrite** — one prompt, deeper not bigger: the same or a smaller deliverable, a harder path. Every added line changes what gets done or how it is checked. The prompt assumes a computer that can install software and reach the data; access that does not exist yet becomes the prompt's first step or is named as a blocker.
   Done when: the checks below pass.

## Reply

```
Altitude: <chosen rung + the access it needs, or n/a because …>
Depth:    <a> / <b> / <c> / <d + threshold>
Range:    <verbs> → <field: technique>, …
Stretch:  <anything beyond the user's stated scope, for them to accept; omit if none>

<the rewritten prompt, in a fenced block, ready to paste>
```

Write the lens lines in the conversation's language and the prompt in the language of the user's original prompt.

## Checks

- Each lens has a concrete answer or a one-line "n/a because …".
- The prompt names its outside judge and pass threshold.
- No line would still read true pasted under a different prompt; rewrite any that would.
- Scope stays inside what the user asked; a bigger idea goes on the Stretch line, not into the prompt.
