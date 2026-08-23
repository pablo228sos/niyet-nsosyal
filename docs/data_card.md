# NIYET intent dataset notes

## Current version

File: `data/intent_seed_v1.csv`

Current size: 96 Turkish examples

Class balance:
- ASK: 24
- FEEDBACK: 24
- COLLABORATE: 24
- DISCUSS: 24

The file is a controlled seed set for development. It is not yet the final evaluation dataset.

## Why we keep source groups

The 96 examples are arranged in 48 source groups. Each group contains two closely related phrasings of the same underlying case. Group IDs are used during splitting so related examples do not land on opposite sides of train and test.

A normal random row split would make the first numbers look better than they should because the model could see a near-paraphrase during training. We avoid that.

## Review status

Every row in v1 is marked `draft seed; team review pending`.

The intended class is already filled so we can develop the training and evaluation pipeline. Before we use this dataset as evidence in the competition report, the team should review the rows and correct unclear labels.

For a validation subset we will keep two independent labels in `label_a` and `label_b`. Disagreements stay visible until they are resolved. If we have enough double-labeled rows, we will report inter-annotator agreement.

## What is not in the dataset

We do not include:
- private messages
- private profile information
- phone numbers or email addresses
- names copied from real users
- posts presented as public data when they were written by the team

## Known limitations

The current seed set is balanced on purpose. Real NSosyal traffic will not have equal class frequencies.

The examples are also relatively short and clear. A real feed will contain ambiguous posts, mixed intents, slang, spelling mistakes, links, media-only posts and posts that do not ask for any response at all.

Because of this, v1 is useful for pipeline development but not enough for a strong final claim about real-world accuracy.

## Before final model evaluation

We need to add:
- ambiguous and negative examples
- spelling and informal Turkish variants
- mixed-intent examples
- a `NONE` or response-not-needed decision before four-way intent classification, or an explicit rule explaining why this is handled separately
- reviewed labels
- final train/validation split policy

The report will distinguish development results from final reviewed results.
