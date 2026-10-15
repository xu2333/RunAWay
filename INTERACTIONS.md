# Two cards meet

The first theater prototype asks a concrete question: **does a short fictional encounter make someone think of a particular friend they want to invite?** This is a design hypothesis, not an established growth effect.

Open `web/dist/theater.html` through the local server in the README. Eight original AI-authored, prewritten scenes work without a model call. They are editorial examples, not live simulations or human conversations. Any two of the 700 catalogue residents can be selected for a manual LLM round trip in one of eight settings. The personal-memory extraction path remains separate.

## Story shape

Six alternating lines form a small arc: a shared task, a concrete interruption, and a result caused by both residents. Behavior should appear in decisions and responses rather than in repeated catchphrases. Neither person is permanently the wise one or the obstacle. The ending should name something they changed together, such as an unexpectedly useful sign or a revised travel plan.

| Preset | Collision | Joint result to inspect |
| --- | --- | --- |
| 明天有限公司，今晚开业 | Deferral × deadline activation | The first customer forces a one-product menu and an immediate duty roster. |
| 这座荒岛支持试营业 | Reversibility × finding demand | A water stall becomes a temporary writing desk. |
| 随便逛，也有自己的表格 | Structure × spontaneous exploration | A travel sheet preserves the return time and leaves room for discovery. |
| 饭局委员会终于开饭 | Eliciting preferences × accepting a sufficient option | Essential constraints get checked before the last table is booked. |
| 杂物山获得了正式地名 | Labels × spatial memory | A temporary label makes a messy location legible to both. |
| 最重要的那个像素 | Visual detail × practical reliability | Observation redirects polish toward a button people can find. |
| 一条龙能读完的通知 | Full context × conclusion first | A useful first line and a detailed reverse side serve both needs. |
| 不会走路的青蛙也能入学 | Flexibility within rules × absurd analogy | A paper frog becomes a valid folding demonstration. |

These rows explain editorial intent. They do not establish model fidelity or that viewers will share.

## Sharing mechanics

- **Recognition:** each side makes a concrete choice someone can recognize.
- **A shared artifact:** one image contains both names, all six lines and the ending. No invented chemistry percentage, rarity or relationship diagnosis.
- **A specific invitation:** “who would take the other role?” makes a natural next action without requiring tagging, rewards or social pressure.
- **Reproducible presets:** a preset link opens the same authored episode. A custom invitation link only restores the cast and setting; the UI explicitly says it does not carry generated dialogue.

The role IDs in links refer only to public fictional catalogue entries. Neither private profiles nor user histories are used. Imported story text is local to the tab. Copying/downloading is explicit; there is no automatic posting, analytics or server storage.

## Check before calling it a good interaction

1. **Observable choices:** can a reviewer point to an action reflecting each card's behavior?
2. **Response dependence:** does a later line address something the other person actually did or said?
3. **Cast sensitivity:** replace one card with a contrasting one while keeping the scene fixed. Does the resulting action change? Merely swapping names in the existing text is not a successful test.
4. **Scene sensitivity:** the same pair in another task should not repeat an identical joke and ending.
5. **Invitation specificity:** can a viewer identify someone they want to send it to, rather than just rating it pleasant?

The browser checks exact cast/scene identity, alternating speakers, six turns, allowed fields and character limits. It does not score the five properties above. Automated judges can assist editorial review, but an uncalibrated judge is not a substitute for observed use or a fidelity experiment. A next experiment can compare paired scenes with isolated cards, distinguish copy/download requests from actual recipient visits, and measure voluntary continuation after an invitation. This prototype does not collect those events.

## Implementation contract

`theater-data.mjs` contains the eight settings and original scripts. `theater-core.mjs` creates narrowly scoped requests from **two** catalogue cards, validates imported JSON and renders local PNGs. `theater.mjs` uses text-only DOM rendering. Changing either cast member or the scene discards the visible result and clears stale export links; a response for an old context is rejected.

The exported theater prompt is fictional role-play, not a personal-memory artifact. No 700-card prompt dump, hidden personality assignment or claim of predicting real relationships is introduced. Public source packaging remains allowlisted.

```sh
node --test tests/theater.test.mjs
```
