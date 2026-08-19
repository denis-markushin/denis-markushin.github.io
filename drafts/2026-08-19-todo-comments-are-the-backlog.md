---
authors:
  - denis
date: 2026-08-19
categories:
  - Tools
tags:
  - kotlin
  - technical-debt
  - automation
  - ci
---

# Your TODO comments are the backlog

There is a `TODO` in one of the codebases I work on that is four years old. The Jira ticket about it
was closed a year and a half ago with the resolution "no longer relevant". Both of them are lying,
but the code is lying less: the workaround the comment describes is still there, still executing on
every request.

Technical debt always ends up with two sources of truth — the comment next to the code and the
ticket in the tracker — and they never converge on their own. I wrote [puzzler] to make the tracker
stop pretending it is one of them.

<!-- more -->

## Two sources of truth, zero agreement

The usual workflow goes like this: you notice a problem while working on something else, you file a
ticket, and you leave a comment like `// see PROJ-1234`. From that moment the two records drift
apart. The ticket gets re-prioritized, bulk-closed during a backlog cleanup, or survives long after
someone quietly fixed the code. The comment stays exactly where the problem is — but nobody who
plans a sprint ever reads it.

The comment has one property the ticket can never have: it lives and dies with the code. Delete the
hack, and the comment describing it disappears in the same commit. No process, no discipline, no
"remember to close the ticket" — the version control system does the bookkeeping.

So instead of trying to keep two sources of truth in sync, [puzzler] demotes one of them:

> The comments are the backlog. The tracker only mirrors them.

This idea is not new — Yegor Bugayenko's [puzzle driven development] and [0pdd] have been filing
tickets from `@todo` markers for years, and puzzler borrows the word *puzzle* from there as an
homage. What is different is the mechanics: no puzzle numbering, no chains linking a puzzle to a
parent ticket, no special markup beyond the `TODO` you already write. How that works is the
interesting part, and most of this post is about it.

## How a run works

puzzler is a CLI that runs in CI on every push. A comment like this:

```kotlin
class Cache {
    // TODO(debt, 30min) [perf]: extract cache into a separate bean
    //   needs TTL and metrics
    val store = mutableMapOf<String, String>()
}
```

becomes an open ticket — with a type mapped from `debt`, the estimate in the body, and the `perf`
label — the moment the commit lands on the default branch. Delete the comment, and the next run
closes the ticket. Nobody files anything, nobody closes anything.

Each run is a five-step pipeline:

```
Scan → Parse → Hash → Reconcile → Apply
```

**Scan** asks `git ls-files` for every tracked file and groups contiguous comment lines into
blocks. The scanner has no idea what programming language it is looking at — it only knows comment
prefixes (`//`, `#`, `--`, `*`, `;`), which is why the same binary handles Kotlin, Python, SQL and
Bash without per-language plugins. **Parse** matches each block's first line against a regexp with
named groups; subject, type, estimate and labels fall out of the match. **Hash** computes each
puzzle's identity — more on that in a second. **Reconcile** diffs the puzzles found in the code
against the tickets currently open in the tracker. **Apply** creates and closes tickets — but only
on the default branch. On a feature branch, a detached HEAD, or with `--dry-run`, the run degrades
to a plan (`created 2, closed 1 (planned only)`) and writes nothing.

Trackers are pluggable: GitHub Issues, GitLab and Jira Server ship built in, and an `exec` hook
covers everything else — puzzler shells out to your script with a JSON request and reads a JSON
response, so a tracker adapter can be twenty lines of Bash.

## What makes a TODO "the same" TODO?

Here is the problem that makes this whole category of tools interesting. On every run, puzzler sees
a fresh snapshot of the code. To decide which tickets to open and which to close, it has to answer:
*is this `TODO` the same one I saw last time?*

File and line number are the obvious answer and the wrong one. Rename a file, extract a class, or
add ten lines above the comment, and a file+line identity would close one ticket and open another —
for a puzzle nobody touched. Refactoring would churn your tracker.

puzzler's answer is that a puzzle *is* its text. Identity is a hash of the normalized subject and
body, and nothing else:

```kotlin
object PuzzleHash {
    private val whitespace = Regex("\\s+")

    fun of(subject: String, description: String): String =
        MessageDigest.getInstance("SHA-256")
            .digest(normalized("$subject\n$description").toByteArray(Charsets.UTF_8))
            .joinToString("") { byte -> "%02x".format(byte) }
            .take(12)

    private fun normalized(text: String): String =
        text.replace("\r\n", "\n")
            .replace('\r', '\n')
            .lineSequence()
            .map { line -> line.trim().replace(whitespace, " ") }
            .filter { line -> line.isNotEmpty() }
            .joinToString("\n")
}
```

That is the entire mechanism — normalization flattens line endings, indentation and runs of
whitespace, so reformatting a comment does not change its identity. No file name, no line number,
no sequence counter. Move the comment across files and the ticket does not blink.

The flip side is a deliberate trade-off: **editing a puzzle's text creates a new puzzle.** Fix a
typo in the subject, and the next run closes the old ticket and opens a new one. I considered
fuzzy matching — similarity thresholds, edit distance — and rejected it, because a fuzzy identity
means you can never predict what a run will do. A hash is brutal but honest: the ticket tracks a
*specific statement about the code*, and if the statement changed, it is a different statement.
Rule of thumb: moving code never touches a ticket; rewording a comment always does.

## A tool that closes tickets has to earn that right

Opening tickets is a safe operation — the worst case is noise. *Closing* them is not. A bug in the
scanner, a typo in the puzzle pattern, or running in the wrong directory all look identical to
puzzler: "the puzzles are gone". Followed naively, that observation closes your entire backlog.

So the reconciler treats its own conclusions with suspicion, in three layers.

**The empty-scan guard.** If the scan finds *zero* puzzles while the tracker still has open
tickets, the run refuses to close anything and exits with an error. An empty scan almost always
means a broken environment — wrong working directory, a pattern that no longer matches anything —
not a heroic commit that resolved every last piece of debt. This guard cannot be overridden, not
even with `--force`. If the last puzzle genuinely left the codebase, you close the final ticket by
hand, once.

**The mass-closure guard.** If a run wants to close more than half of the currently open tickets,
it stops and asks for `--force`. A sudden wave of closures is the signature of a broken hash — a
regex change, a normalization bug — or a tracker query returning the wrong scope. When it *is*
intended (you just deleted a deprecated module), `--force` says so explicitly.

**Previews are fearless, real runs are paranoid.** During `--dry-run` or on a non-default branch,
a tripped guard is only a warning — a preview has nothing to lose by showing you what the guard
found, so it completes and exits `0`. The same violation on a real run fails with a dedicated exit
code. You get full information when it is safe, and a hard stop when it is not.

None of this is sophisticated computer science. But I have come to think it is the actual product:
anyone can write a script that files tickets from grep output; the hard part is a tool you can
point at a live tracker on every push and not think about it again.

## Interlude: the two invisible bugs

One war story from the commit history, because it is instructive. A colleague wrote comments in
Russian: `// TODO(баг): почистить кэш` in a file named `Кэш.kt`. Zero tickets appeared. Nothing
failed, nothing warned — the puzzles simply did not exist.

Two independent bugs, both invisible:

1. The `type` group in the default pattern used an ASCII-only character class, so `TODO(баг)` did
   not match the pattern at all. Not "matched with a mangled type" — matched *nothing*, silently.
   The fix widened the class to Unicode letters: `[\p{L}\p{N}_-]+`.
2. `git ls-files` by default prints non-ASCII paths octal-escaped in quotes — `"\320\232\321\215\321\210.kt"`
   instead of `Кэш.kt`. The scanner asked the filesystem for a file literally named with
   backslashes, found nothing, and skipped it. The fix is one flag: `git -c core.quotePath=false ls-files`.

The lesson generalizes to any scanner-shaped tool: the expensive bugs are the ones where nothing
crashes. A parser that throws on weird input gets fixed the same week; a parser that silently
matches nothing can ship for months. It is also why puzzler's guards exist — when your failure
mode is "quietly sees less than it should", you want an independent mechanism asking "does this
result even make sense?".

## Try it

puzzler ships as a single Docker image, nothing else — no native binary, no Gradle plugin. A
five-minute trial against your own repo:

```yaml
# .puzzler.yml
tracker:
  type: github
  project: your-org/your-repo
  token: ${PUZZLER_TOKEN}
repo:
  name: your-repo
```

```bash
docker run --rm -v "$PWD:/repo" -w /repo -e PUZZLER_TOKEN \
  ghcr.io/denis-markushin/puzzler:1 --dry-run
```

`--dry-run` is guaranteed read-only: it prints the plan — what would be created and closed — and
never touches the tracker. Once the plan looks right, drop the flag in a default-branch CI job and
you are done; the [CI recipes] cover GitHub Actions, GitLab CI and Jenkins.

Honest status report: this is version 0.1. I use it myself, and the primary deployment it was
built around is code in GitLab with tickets in Jira Server (there is a [worked example] for
exactly that setup). Jira Cloud is deliberately not supported yet, and if your tracker is
something else entirely, the [exec hook] is the escape hatch.

The source is on [GitHub][puzzler]. If your codebase also has a four-year-old `TODO` whose ticket
died long ago — point a `--dry-run` at it and see what your comments have been trying to tell you.

[puzzler]: https://github.com/denis-markushin/puzzler
[puzzle driven development]: https://www.yegor256.com/2010/03/04/pdd.html
[0pdd]: https://www.0pdd.com
[CI recipes]: https://github.com/denis-markushin/puzzler/blob/main/docs/ci-recipes.md
[worked example]: https://github.com/denis-markushin/puzzler/blob/main/docs/gitlab-to-jira.md
[exec hook]: https://github.com/denis-markushin/puzzler/blob/main/docs/exec-hook.md
