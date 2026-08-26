# GitHub pull-request integration

The root `action.yml` compares two graph files, builds a removal-aware impact report, and appends it to GitHub Job Summary.

```yaml
permissions:
  contents: read
  pull-requests: write

steps:
  - uses: actions/checkout@v4
  - uses: dkharlanau/enterprise-change-graph@main
    with:
      before: path/to/before.yaml
      after: path/to/after.yaml
      comment: 'true'
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

With `comment: 'true'`, the action finds the existing `<!-- enterprise-change-graph -->` PR comment and updates it. This keeps one current change-review artifact instead of creating a new bot comment for every push.

If comment mode is disabled, read access is sufficient. The generated report path is also available as the `report` output.
