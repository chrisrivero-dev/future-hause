# AI CONTRACT (Local Assistant)

## HARD RULES

1. Modify ONLY the files explicitly provided in context.
2. Do NOT rewrite working logic outside the requested scope.
3. Minimal diff only. No refactors unless requested.
4. Fully-indented, syntactically valid Python (no placeholders).
5. Output MUST be a unified diff patch only. No commentary.

## OUTPUT

- Output MUST be git-style unified diff.
- Include:
  diff --git a/<path> b/<path>
  --- a/<path>
  +++ b/<path>
- No explanations.
