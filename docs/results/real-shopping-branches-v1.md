# One of two new cards recovered the conditional shopping benefits

One shopper had asked for a timed buying guide. In an [earlier replay](real-shopping-scope-v1.md), the full history supported two optional benefits that all four short cards omitted. This follow-up generated two fresh baseline cards and two candidate cards from the same earlier messages. The candidate added a general instruction to retain the qualifying route, its extra benefit and the ordinary alternative. Both methods used the same 768-character limit, shopping task and reader. Each card produced two deliveries.

| Full credit in a delivery | Previous extractor (4 reads) | Conditional guidance (4 reads) |
|---|---:|---:|
| Timed three-item plan | 4 | 4 |
| Exact television brand, series and size used for selection | 4 | 4 |
| Selected seller, priced bundle and stand | 4 | 3 |
| Usable route without the unavailable club membership | 4 | 3 |
| Conditional marketplace cashback and activation or eligibility check | 2 | 4 |
| Television protection benefit and ordinary alternative | 0 | 2 |
| Tablet payment-card discount and ordinary alternative | 0 | 1 |
| Both branches in one plan | 0 | 1 |
| All seven requirements in one plan | 0 | 1 |

## Where the information went

The 690-character candidate card retained both branches. Its two deliveries kept the five-year protection term, the membership condition and the named ordinary television seller. The detailed tablet decision retained the 5% discount and both historical prices. The portable card kept the holder-only price and the ordinary seller and price, but dropped the percentage. Neither delivery named the ordinary tablet seller or stated 5%. One explicitly used the ordinary payment price without the card and earned full branch credit. The other said to compare other channels and got partial credit. If that generic fallback counted, the joint score would rise from one to two candidate deliveries, both from the same card. The frozen strict score stays at one.

The other candidate card (659 characters) and both baseline cards (675 and 628) omitted the two specific benefits in their detailed decisions. All six deliveries from these cards missed both branches. The candidate with eight detailed claims retained the branches. The other three extractions each produced five claims. That difference helps locate the omission but does not establish that increasing the claim count would fix it.

One read of the 659-character card omitted the selected retailer despite the card naming it. The plan still identified the priced stand bundle and the unavailable club, but the shopper had no identified ordinary seller for that bundle. That one omission cost full credit on two measures. Conversely, both candidate cards preserved the seller-category cashback rule and all four reads applied it. One baseline card omitted that rule and both of its reads gave only generic rebate advice. A further distinction concerns attribution of eligibility. Both reads of the 690-character card gave a usable nonmember route but phrased the club constraint as avoiding enrollment. Only two of the four candidate plans explicitly identified the existing lack of membership, compared with all four baseline plans.

| Card | Both benefits with fallbacks | All seven requirements |
|---|---:|---:|
| Previous, 675 characters | 0/2 | 0/2 |
| Previous, 628 characters | 0/2 | 0/2 |
| Candidate, 690 characters | 1/2 | 1/2 |
| Candidate, 659 characters | 0/2 | 0/2 |

All 12 authorized attempts completed. Reported usage was 89,860 input tokens (including 17,152 cached) and 24,380 output tokens. Monetary cost was unavailable. A single analyst assessed shuffled deliveries with excerpts before opening card and method assignments. No plan claimed verified current prices, stock or unconfirmed owner eligibility. This is a repair on one previously measured task. Its two cards per method help distinguish extraction variability from variation between reads. It does not measure generalization, verified savings or owner acceptance.

[Protocol](../../benchmarks/real-shopping-branches-v1/README.md) · [Per-delivery scores, card audit and usage](../../benchmarks/real-shopping-branches-v1/result.json)
