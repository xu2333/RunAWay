# One-shot budget failures and observed losses

These are original one-shot candidates. No rejected card was repaired,
truncated, exported as valid or read. Character counts are not tokens.

| Person | Requested budget | Actual packed characters | Result |
| --- | ---: | ---: | --- |
| h17 | 384 | 654 | Rejected: whole budget |
| h42 | 512 | 671 | Rejected: whole budget |
| h68 | 768 | 783 | Rejected: whole budget |
| h93 | 384 | 714 | Rejected: whole budget |
| h17 | 512 | 616 | Rejected: whole budget |
| h42 | 768 | 745 | Valid |
| h68 | 384 | 732 | Rejected: whole budget |
| h93 | 512 | 703 | Rejected: whole budget |
| h17 | 768 | 747 | Valid |
| h42 | 384 | 781 | Rejected: whole budget |
| h68 | 512 | 628 | Rejected: whole budget |
| h93 | 768 | 762 | Valid |

The existing greedy literal packer saved0characters on all12answers.
No independently optimized minimum is claimed.

## Budget 384

Observed own-reader errors: 0. Missing planned own cells: 80.

- h17: 20 missing cells; 13 known, 7 U.
- h42: 20 missing cells; 13 known, 7 U.
- h68: 20 missing cells; 12 known, 8 U.
- h93: 20 missing cells; 14 known, 6 U.

Missing cells are end-to-end failures, not observed wrong model choices.

## Budget 512

Observed own-reader errors: 0. Missing planned own cells: 80.

- h17: 20 missing cells; 13 known, 7 U.
- h42: 20 missing cells; 13 known, 7 U.
- h68: 20 missing cells; 12 known, 8 U.
- h93: 20 missing cells; 14 known, 6 U.

Missing cells are end-to-end failures, not observed wrong model choices.

## Budget 768

Observed own-reader errors: 0. Missing planned own cells: 20.

- h68: 20 missing cells; 12 known, 8 U.

Missing cells are end-to-end failures, not observed wrong model choices.
