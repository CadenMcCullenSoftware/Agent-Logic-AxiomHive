---
name: Pull Request Template
about: Template for pull requests
title: ""
labels: ""
assignees: ""
---

## Summary

Briefly describe what this pull request changes and why.

## Related issue

Fixes # (issue number, if applicable)

## Checklist

- [ ] I have read the [CONTRIBUTING](CONTRIBUTING.md) guide
- [ ] My change is scoped to a single concern
- [ ] I have added or updated tests for any change to `catalog_engine.py`
- [ ] I have updated documentation when behavior or the schema changes
- [ ] `python3 -m unittest -v` passes
- [ ] `python3 catalog_engine.py --tool validate` passes
- [ ] `python3 catalog_engine.py --tool selftest --database :memory:` passes
- [ ] No secrets, keys, or credentials are included

## Additional context

Add any other context or screenshots here.