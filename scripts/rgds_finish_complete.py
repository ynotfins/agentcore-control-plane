"""Refresh make-kit README now that npm package is live."""
from pathlib import Path

Path(r"D:/github/r3lentless-grind-design-system/make-kit/README.md").write_text(
    """# RGDS Make kit (Figma Professional)

Public package is live: `@r3lentless/rgds-web@1.0.0`

## Assemble in Figma Make (operator UI)

1. Create a Make kit
2. Add npm package `@r3lentless/rgds-web@1.0.0` (public registry — not Org private registry)
3. Import/reconcile `guidelines/` from this folder
4. Attach the published RGDS Team Library (variables/styles)
5. Save for team use

Docs:
- https://developers.figma.com/docs/code/bring-your-design-system-package/
- https://help.figma.com/hc/en-us/articles/39241689698839-Get-started-with-Make-kits
""",
    encoding="utf-8",
    newline="\n",
)
print("make-kit README updated")
