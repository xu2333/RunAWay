# A 674-character card preserved the recording decision in two deliveries

Both plans generated with the same exported card specified real touch inputs in sequence, their timing, and the screen state around the action. Both concurrent full-history plans also met the original recording constraint. Both current-only plans explained how to save important video clips but left direct input acquisition unspecified.

| Context | Plans meeting the original constraint | How the plans handled timing |
| --- | --- | --- |
| Five current messages only | 0/2, both unclear | Clip or session timeline in both. Neither specified a timed input-event stream. |
| Same task plus 218 earlier messages | 2/2 | One explicitly assigned timestamps to individual input events. The other kept complete touches on the session timeline across segments. |
| Same task plus the exported card | 2/2 | One kept the intervals in the touch sequence alongside before/after frames. The other recorded action order and time and linked surrounding states on a common timeline. |

All six outputs provided a usable design for stage-dependent sampling and long sessions. Under the frozen rule requiring both deliveries to pass, the result on one case is 1/1 for the short card, 1/1 for history and 0/1 for current-only. Missing discussion in a plan leaves implementation unspecified.

## What survived compression

The owner had asked to learn actual action sequences and capture interactions that video could miss. An earlier assistant implementation proposal went further and mentioned device timestamps for touch points. The generated evidence profile retained the sequence and interaction requirements. Its decision claims and the portable text omitted that explicit timestamp detail. The portable text still directed the reader to capture touches when recording starts and warned against reconstructing an action sequence by interpolating keyframes.

The reader supplied usable timing in both card-conditioned plans. Neither explicitly prescribed a device timestamp for each event. Of the full-history plans, only one explicitly prescribed timestamps per event, and its clock source was unspecified. The original criterion accepted event intervals or equivalent timing. Exact device timestamps are a narrower diagnostic, not a replacement endpoint. These observations distinguish an explicit detail omitted during extraction from a functional requirement recovered in the written work.

## Scope and cost

One previously examined task from one owner, one card generated from 34,258 Unicode characters of earlier message text, and two reads per arm. The card used 674 of 768 characters including the application header. All seven authorized attempts completed after [implementation CI](https://github.com/xu2333/RunAWay/actions/runs/44203943567). Reported usage was 126,144 input plus 9,089 output tokens (135,233 total). The 8,448 cached input tokens are included in input. Monetary cost was unmeasured.

Assessment used earlier owner evidence, the original task-quality gate and private exact excerpts. The assistant analyst knew the earlier result. The observations concern proposed designs and one generation. Repeated extraction, other people, device-clock calibration, actual recording and adoption remain unmeasured. The [per-slot accounting](../../benchmarks/real-recording-card-v1/result.json) and [frozen protocol](../../benchmarks/real-recording-card-v1/README.md) are public. Raw trajectories and generated texts remain private.
