# Product flow

The product should feel like a small extension of posting and replying, not a separate matching app.

## 1. Author creates a normal post

The user writes a post in the existing composer.

NIYET runs the response-needed gate in the background.

If the post looks like a normal update, nothing changes. The post is published normally.

If the post appears to seek a response, the composer shows a small suggestion before publishing:

`Bu gönderi için yanıt mı arıyorsun?`

Suggested intent:
- Yardım iste
- Geri bildirim iste
- Birlikte çalışacak kişi ara
- Tartışma başlat

The user can accept, change or dismiss the suggestion.

## 2. Intent becomes eligible for routing

After confirmation, the request enters the open-intent queue.

The platform does not send it to every relevant user. Candidate retrieval narrows the pool first.

Before scoring, the system removes:
- users who did not opt in
- blocked relationships
- users outside their current attention budget
- candidates that fail safety rules

## 3. Candidate allocation

The allocator receives a bounded set of open intents and candidate responders.

Instead of taking the best responder for each post independently, NIYET allocates the batch together. This avoids spending the same scarce responder on a request that had an almost equally good alternative while another request has no alternative.

An intent may remain unmatched when every eligible candidate is weak.

## 4. Responder sees a request card

The request appears as a suggestion, not as an automatic direct message.

The card should show:
- original post text
- intent type
- topic
- why the request was suggested
- `Yanıtla`
- `Geç`
- `Bu konuda istek alma`

We should not show a fake precision such as `93% match` to the user. Model scores are internal ranking signals, not a guarantee of usefulness.

## 5. Interaction happens in normal NSosyal surfaces

If the responder accepts, they reply through the normal post/reply flow. NIYET does not need a separate messaging system.

## 6. Outcome feedback

After a response, the author can give a lightweight outcome signal:
- Faydalı oldu
- Sorunum çözüldü
- İlgili değildi

The responder can also say that the request was not relevant to their interests.

These signals can later improve matching. They should not be required to publish or reply.

## Correction points

A model can be wrong at several stages. The interface should make correction cheap:
- wrong response-needed detection: dismiss suggestion
- wrong intent type: change it before publishing
- wrong responder topic: skip and adjust topic preference
- bad match: mark not relevant
- too many requests: lower attention budget or pause routing

## Accessibility requirements for the prototype

- all actions work with keyboard only
- visible focus state
- semantic button labels, not icon-only controls
- intent is never communicated only by color
- minimum readable contrast for text and controls
- status changes announced to screen readers
- no forced time limit for accepting a request
- reduced-motion preference respected for optional animation

## Usability test tasks

We can test the flow with five short tasks:
1. publish a help-seeking post and correct the detected intent
2. publish a normal update without enabling NIYET
3. accept a routed request and reply
4. skip an irrelevant request and change topic preferences
5. pause incoming NIYET requests

For each task we record completion, errors, time, one short difficulty rating and comments. We should fix clear usability problems before the final presentation and keep both positive and negative test feedback.
