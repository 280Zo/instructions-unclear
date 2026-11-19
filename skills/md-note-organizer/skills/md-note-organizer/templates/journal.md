# Journal template

Mostly for remembering what happened and enjoying the memory later. The entry tells the story in the user's voice, with the small, specific details that bring it back.

## Interview first

Don't write the entry from the first message. Reply with three to five questions about what the user actually wrote. Ask for the details that bring a memory back: who was there, where, what it looked, sounded or tasted like, what someone said, and the moment worth remembering. Then:

- Check assumptions before using them ("Was this last weekend, the 14th and 15th?").
- Ask open questions that don't suggest an answer. "What made the pancakes memorable?" is fine. "Were they your grandmother's recipe?" puts words in the user's mouth.
- Ask another round only when an answer opens something worth asking about. Stop when the user says "write it" or the answers are enough.

The entry uses only details the user gave or confirmed. Never fill a gap with something plausible.

## Voice

When the user points to a writing sample (a past entry or anything casual they wrote), work in this order:

1. Read the sample and note its traits to yourself:
   - sentence length and rhythm (short and clipped, or long and run-on)
   - how a story opens and how it ends (a setup line, a verdict, a joke)
   - humor and self-deprecation
   - swearing
   - emphasis habits (caps, ellipses, exclamation marks)
   - rhetorical questions
   - how much they address the reader
2. Write the entry with those traits. If the sample swears, the entry can swear at about the same rate. If it ends stories with a verdict or a rating, the entry can too, but only one built from the user's answers.
3. The traits shape how things are said, never what happened. Every event, feeling and detail still comes from the user's answers.
   - **Allowed:** changing word order and sentence length, emphasis, a setup line that announces a story the answers tell, a rhetorical question that restates a fact from the answers, and a closing verdict built from the answers.
   - **Not allowed:** a new image, simile, repetition, motive, reaction or feeling. That includes the dog's opinion, "again and again", "like it was keeping an eye on us", and "we weren't about to waste them".

   Before replying, check each sentence: if a detail can't be pointed to in the answers, cut it.
4. Apply `humanizer` with the sample as its voice sample, so it keeps those traits and only removes AI tells.

Without a sample, write plain, warm first person, keeping the user's opinions, humor, asides and mixed feelings.

Refer to people by name, or by the pronoun the user used for them. Don't assign a pronoun the user didn't use.

## Frontmatter

Shared properties, plus:

- `date`: the day it happened. `created` is when it was written.
- `people`: list of links to the people in the story.
- `places`: list of links to the places.

## Body

- First-person paragraphs telling the story. No sections before the story and no bullet lists.
- Embed photos the user supplied where they fit the story: `![[cabin-dock.jpg]]`.
- End with `## Worth remembering`: a line or two the user would want to find again, such as a quote, a feeling or a first.

## Example

```markdown
---
type: journal
title: Cabin weekend with Sam
created: 2026-11-18
date: 2026-11-15
people: ["[[Sam]]"]
places: ["[[Lake cabin]]"]
source: journal interview
tags: [trips]
---

[[Sam]] insisted on making the pancakes, which meant the first three went to the dog. By the fourth he had it figured out, and we ate on the porch with our feet on the railing.

That evening we walked down to the dock and stayed until the light went orange and then gone. Neither of us said much.

## Worth remembering
Sam, holding up pancake number four: "This is the one we tell people about."
```
