# GitHub pull-request integration

The root `action.yml` is a composite action that compares two graph files and appends a removal-aware impact report to GitHub Job Summary.

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: dkharlanau/enterprise-change-graph@main
    with:
      before: path/to/before.yaml
      after: path/to/after.yaml
```

The action needs read access only. Teams wanting a persistent PR comment can use `github_pr_comment()` with their own authenticated transport.
