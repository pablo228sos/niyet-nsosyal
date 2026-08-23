# Usability test protocol

Purpose: test whether a user understands NIYET inside the NSosyal-style feed without receiving an explanation first.

Target: 6 to 10 participants for the first competition test.

Time per participant: about 5 to 7 minutes.

The test should use the deployed prototype on the participant's own phone or laptop when possible.

## Before the test

Do not explain what ASK, FEEDBACK, COLLABORATE or DISCUSS mean before the participant sees the interface.

Tell the participant only:

"This is a concept feature for a social network. Please use it as if you had opened it normally. I will give you a few tasks. Think aloud if you can."

Record:

- device type
- language used: EN or TR
- whether the participant has used social media daily in the last month

Do not collect names, account handles or private messages.

## Tasks

### Task 1: Normal post

Instruction:

"Publish the normal benchmark update using the provided demo option."

Success condition:

- participant selects the normal-post example
- understands that NIYET does not need to route it
- publishes without trying to force an intent

Observe:

- whether NIYET staying out of the flow is clear
- whether the user waits for an AI panel that never appears

### Task 2: Ask for help

Instruction:

"Use the demo to ask for help with the line-following robot. Route it to someone who may help."

Success condition:

- response-needed state appears
- participant understands the suggested intent
- participant confirms or changes the intent
- participant uses Route with NIYET
- responder preview becomes understandable

Observe:

- whether the user understands that routing is optional
- whether the user mistakes a development score for a probability
- whether the user understands why a responder was selected

### Task 3: Correct the model

Instruction:

"Imagine the suggested intent is wrong. Change it to another intent before routing."

Success condition:

- participant finds the intent choices without help
- understands that their choice overrides the suggestion

### Task 4: Responder control

Instruction:

"You are now the responder. You do not want more requests today. Stop new routing requests."

Success condition:

- participant finds the routing switch
- understands attention budget and pause state

### Task 5: Technical transparency

Instruction:

"Find the technical information about why the last route was produced."

Success condition:

- participant finds Technical details
- understands that the displayed numerical values are development diagnostics, not calibrated probabilities

This task is mainly for jury/demo transparency. It does not have to be a primary consumer action.

## Metrics

For every task record:

- completed without help: yes/no
- time to completion in seconds
- wrong clicks before completion
- facilitator hint needed: yes/no
- one short observation

After all tasks ask three 1-5 questions:

1. "I understood when NIYET would become active."
2. "I understood that I could control or stop routing."
3. "I understood why a responder was selected."

Then ask:

"What was the most confusing part?"

## Result table

Use one row per participant:

| ID | Device | Lang | T1 | T2 | T3 | T4 | T5 | Hints | Main confusion |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| P01 | | | | | | | | | |

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

This creates a direct evidence chain for the UI/UX section of the Technical Report.
