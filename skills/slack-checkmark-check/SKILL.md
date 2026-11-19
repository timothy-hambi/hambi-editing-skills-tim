---
name: slack-checkmark-check
description: Checks who has and hasn't reacted with a ✅ check mark on any Slack message, from a pasted Slack message link. Use whenever Tim pastes a Slack message link and asks who has ticked, checked, ✅'d or acknowledged it, e.g. "check mark check on this", "who's ticked this", "who hasn't acknowledged", "run the ✅ check", "who still needs to react", or just pastes a Slack link with "check" or "ticks". Typical uses are allocation posts, handover/handback messages, deadline reminders and announcements during Acting PPM cover. Read-only; never sends anything.
---

# Slack ✅ check

Tim pastes a Slack message link. Report who has reacted with a check mark and who hasn't, with no back-and-forth.

## 1. Parse the link

Format: `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<DIGITS>`

- `channel_id` = the `C…`/`G…`/`D…` segment.
- `message_ts` = the digits after `p`, with a decimal point inserted before the last 6 digits.
  `p1731480000123456` → `1731480000.123456`
- If the link has `?thread_ts=…&cid=…`, the message is a thread reply. Still use the `p…` value as `message_ts`; keep `thread_ts` for reading the message in step 3.

If the link won't parse, ask Tim for the link again in one line. Don't guess.

## 2. Get the reactions

Call `slack_get_reactions(channel_id, message_ts)`.

Count these as ✅ (any of them): `white_check_mark`, `heavy_check_mark`, `ballot_box_with_check`, `check`, plus any custom emoji whose name contains `check`, `tick` or `done`. Note which custom ones you counted.

Everyone who reacted with something else but no check mark goes in a separate "Reacted, no ✅" group (e.g. 👀 often means "seen, not done").

## 3. Work out who was expected to react

Read the message itself: `slack_read_thread(channel_id, message_ts = thread_ts or message_ts)` and find the target message by its ts.

Expected list, in this order:

1. **People @mentioned** in the message (`<@U…>`). Use them only.
2. **@here / @channel / @everyone, a user group, or no mentions at all**: everyone in the channel via `slack_list_channel_members` (concise, bots excluded, page through every cursor).

Always remove the message author from the expected list. If Tim's request names people ("just check the editors", "only Ana and Joel"), use those instead.

If the channel is very large (40+ members) and nobody was mentioned, say so at the top of the report, since many non-reactors may not be relevant.

## 4. Report

Reply in chat, short, in this shape:

```
✅ check: <first ~8 words of the message>… (#channel, posted <day date, time UK / PH>)

Done (n/total): Name, Name, Name
Waiting (n): Name, Name
Reacted, no ✅: Name (👀)
```

- Names: display names, alphabetical.
- If everyone has ticked, say so in one line instead of the lists.
- If there are no reactions at all, say "No reactions yet" and list everyone waiting.
- Note any expected person who's deactivated or no longer in the channel.

## 5. Offer a nudge (don't send)

If anyone is waiting, end with one line offering a nudge. If Tim says yes, write a short thread reply that @mentions only the people waiting: blame-neutral, conversational, no guilt-tripping. Example:

> Hey @Name @Name, quick one: could you pop a ✅ on the message above once you've seen it? Thanks!

Show the draft in chat. Only save it to Slack as a draft if Tim asks, and never send it. Sending a message needs Tim's explicit go-ahead.

## Rules

- Read-only. Never add or remove reactions, never send messages.
- Don't comment on why someone hasn't reacted (time zones, leave, etc.) unless Tim asks.
- If a Slack call fails with an access or `not_in_channel` error, tell Tim in one line that Claude can't see that channel with his Slack connection.
