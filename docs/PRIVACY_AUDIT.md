# Publication privacy review

Reviewed on 20 October 2026.

## Published source

The source publication was checked for common API-key and token formats, private-key
headers, credential-bearing URLs, hardcoded secret assignments, personal home-directory
paths, runtime databases, environment files, local settings, and logs. No matching
credentials or private runtime files were found in the reviewed source snapshot.

Upstream author contact details in third-party license notices are retained as required.
Repository links use the public GitHub account name.

## Preview data

Public screenshots now use synthetic demonstration readings and fresh temporary settings.
The preview generator does not discover hardware or read personal settings or history.
Image metadata was checked; no EXIF, location, or author tags were found. Local benchmark
results have been replaced with a reproducible methodology.

Earlier commits contain the original sensor previews and local benchmark figures.
Changing the current files does not erase those earlier revisions or third-party copies.

## GitHub identity and history

The reviewed commit history uses GitHub no-reply email addresses. GitHub account names
and configured commit author names remain public metadata. These are separate from the
project's source files. Removing them from existing history requires rewriting Git
history; GitHub may retain old commit URLs and cached copies after a rewrite.

## Ongoing checks

Source export now rejects common private file types, user home paths, and credential
patterns. Linux CI builds and scans the publication archive. To check a source archive:

```bash
python -m tools.privacy_check dist/wattpin-0.4.4-github-source.zip
```

An optional `--private-term` argument can check an additional local identifier without
printing its value. Do not put private search terms in public CI configuration.

Pattern scans cannot guarantee that every possible secret or identifying detail has
been detected. Review new files and screenshots before publishing them.
