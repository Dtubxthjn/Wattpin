# Security and privacy

Wattpin runs as the logged-in user. It does not change sensor permissions, listen on
network ports, require an account, upload telemetry or execute meter-file contents.
Only use a live meter JSON file supplied by a bridge you trust. Power readings and
timestamps are local private data; CSV exports may reveal work habits.

For security reports, use a private channel to the repository maintainer once the project
is published. A public vulnerability-reporting address has not been configured. Do not
include credentials, private database files or unredacted environment dumps in reports.

Supported release series: 0.4.x (beta). Security-sensitive changes should include a regression
test and must preserve the unprivileged collection model.
