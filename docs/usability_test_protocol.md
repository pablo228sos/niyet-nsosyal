# Usability test protocol

Purpose: test whether a user understands NIYET inside the NSosyal-style feed without receiving an explanation first.

Target: 6 to 10 participants for the first competition test.

Time per participant: about 6 to 8 minutes.

The test should use the deployed prototype on the participant's own phone or laptop when possible.

## Before the test

Do not explain ASK, FEEDBACK, COLLABORATE or DISCUSS before the participant sees the interface.

Tell the participant only:

"This is a concept feature for a social network. Please use it as if you had opened it normally. I will give you a few tasks. Think aloud if you can."

Record:

- device type
- language used: EN or TR
- approximate daily social-media use

Do not collect names, account handles or private messages.

## Tasks

### Task 1: Normal post

Instruction:

"Publish the normal benchmark update using the provided demo option."

Success condition:

- participant selects the normal-post example
- understands that NIYET does not need to route it
- publishes without trying to force an intent

### Task 2: Ask for help

Instruction:

"Use the demo to ask for help with the line-following robot. Route it to someone who may help."

Success condition:

- response-needed state appears
- participant understands the suggested intent
- participant confirms or changes the intent
- participant uses Route with NIYET
- responder preview is understandable

### Task 3: Correct the model

Instruction:

"Imagine the suggested intent is wrong. Change it to another intent before routing."

Success condition:

- participant finds the intent choices without help
- understands that their choice overrides the suggestion

### Task 4: Recover from a missed activation

Instruction:

"Imagine this post really needs a response, but NIYET did not activate automatically. Turn NIYET on for this post yourself."

Success condition:

- participant finds the manual `Use NIYET anyway` path
- participant can choose an intent and continue routing

This specifically tests the correction path for a false-negative response gate.

### Task 5: Responder control

Instruction:

"You are now the responder. Accept the current request, then stop new routing requests."

Success condition:

- participant finds Accept
- understands that remaining session capacity changes
- participant finds the routing switch and pauses new requests

### Task 6: Explainability

Instruction:

"Why did NIYET choose this responder? Find the information in the interface."

Success condition:

- participant finds the match explanation / Technical details
- can describe the reason in their own words
- understands that numerical values are development diagnostics, not calibrated probabilities

This task is mainly for transparency and the technical demo. It does not need to be a primary consumer action.

## Metrics

For every task record:

- completed without help: yes/no
- time to completion in seconds
- wrong clicks before completion
- facilitator hint needed: yes/no
- one short observation

After all tasks ask three 1-5 questions:

1. "I understood when NIYET would become active."
2. "I understood that I could correct or stop NIYET."
3. "I understood why a responder was selected."

Then ask:

"What was the most confusing part?"

## Result table

Use `data/usability_results_template.csv`. Use anonymous IDs such as P01, P02 and P03.

Do not place participant names in the public repository.

## What counts as a design issue

A problem is prioritized when:

- at least two participants fail or hesitate on the same action
- one participant makes a high-risk misunderstanding, such as thinking routing is automatic
- a keyboard or mobile interaction becomes impossible
- users interpret a development diagnostic as a real probability

## After the test

For each change record:

`Observed problem -> design change -> reason`

The final report should include actual completion rates and the main fixes made because of observed behavior. Positive comments alone are not a usability result.
