# Contributing

New revivals and improvements to existing fonts use the same source format,
build commands, and review process. A focused correction to a single letter is
as welcome as a complete alphabet.

1. Fork this repository and clone your fork.
2. Create a branch: `git switch -c improve/nero-j` or `git switch -c add/example-1890`.
3. Set up Python using the [README](README.md#build-the-collection).
4. Follow the [workflow](docs/WORKFLOW.md) to add or improve a family.
5. Run the checks below and inspect the specimen PDFs and browser preview.
6. Commit the source, generated files, and changelog. Push your branch and open
   a pull request against this repository's `main` branch.

```sh
python scripts/fontrevival.py build
python scripts/fontrevival.py check
python -m unittest discover -s tests
```

## What to include

- The historical source, page number, link, and documented rights basis.
- Editable source and a short account of observed and reconstructed forms.
- Rebuilt desktop/web fonts, specimen proofs, and an updated family changelog.
- For revisions, a version increase and before/after proof focused on the change.
- For LLM assistance, the tool/model if known and enough method notes to continue
  the work. A full chat transcript is unnecessary.

Never use a modern proprietary font as tracing material. Submit only material
you can share on the terms recorded in the project. By submitting a contribution,
you agree to license your original contributions under the [MIT License](LICENSE).
Historical material keeps its documented public-domain status.

## Review

Reviewers compare the outlines with the cited sources, check spacing and accents,
inspect proofs at several sizes, and review the build checks. Automated checks
establish consistency; visual review establishes quality and historical fidelity.
Keep feedback specific and respectful. If a historical form is uncertain, record
the uncertainty and the reasoning behind the reconstruction.

Use an issue to suggest a typeface, report a bad glyph, or provide a better source.
For glyph reports, include the character, font version, sample text, size, and
application. Screenshots or PDFs help reproduce the problem.
