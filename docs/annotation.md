# Intent annotation guide

We use four labels in the first classifier. The label should describe what kind of response the author is trying to get from other people, not only the topic of the post.

## ASK

Use ASK when the author wants an answer, explanation or practical help with a specific problem.

Example: `ESP32 kartım Wi-Fi bağlantısını sürekli kaybediyor. Nereden başlamalıyım?`

Do not use ASK for a broad opinion question where there is no concrete problem to solve. That is usually DISCUSS.

## FEEDBACK

Use FEEDBACK when the author shows an idea, design, text, project or decision and wants evaluation or suggestions.

Example: `Bu ana sayfa tasarımında sizce ilk değiştirmem gereken şey ne?`

A request for a direct technical fix is ASK, even if the user also describes what they built.

## COLLABORATE

Use COLLABORATE when the main goal is to find another person to build, research, organize or work on something together.

Example: `Robotik projemiz için görüntü işleme bilen bir ekip arkadaşı arıyoruz.`

Requests for one-off advice are not COLLABORATE.

## DISCUSS

Use DISCUSS when the author wants an open exchange of views and there is no single answer or concrete deliverable.

Example: `Sizce küçük ekiplerde açık kaynak model kullanmak uzun vadede daha mantıklı mı?`

## Annotation rules

1. Read the full text before choosing a label.
2. Choose the author's main intent. Do not assign multiple labels in v1.
3. If the intent is unclear, leave the individual label blank and add a note instead of guessing.
4. Keep a source type and source group for every example.
5. Related examples, paraphrases and examples derived from the same seed must share the same source group. We will use the group when splitting the dataset so near-duplicates do not cross train and test sets.
6. Do not copy private messages, private profile data or personal contact details into the dataset.
7. For the validation subset, two team members label the text independently before seeing each other's answer.
8. If the two labels disagree, discuss the example and record the resolved label in `final_label`. Do not silently overwrite the original labels.
9. We do not report model results on a validation set until its labels have been reviewed.

## Source types

- `public`: public content used under our data collection rules, with identifying details removed when needed
- `team_written`: examples written directly by the team to cover a missing case
- `controlled_seed`: controlled examples created to test a particular wording or edge case

The source type is not a quality score. It is there so we can audit where the dataset came from.
