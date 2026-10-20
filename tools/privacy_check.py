"""Check a publication ZIP without printing credential contents."""
from pathlib import PurePosixPath
import argparse
import gzip
import re
import zipfile

PATTERNS = {
    'private key': rb'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----',
    'GitHub token': rb'(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,})',
    'AWS access key': rb'(?:AKIA|ASIA)[A-Z0-9]{16}',
    'API token': rb'(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}|xox[baprs]-[A-Za-z0-9-]{20,})',
    'JWT token': rb'eyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}',
    'credentialed URL': rb'https?://[^/\s:@]+:[^/\s@]+@',
    'personal home path': rb'(?:/home/|/Users/)[A-Za-z0-9_.-]+/',
    'Windows user path': rb'[A-Z]:\\Users\\[A-Za-z0-9_.-]+\\',
    'hardcoded secret': rb'''(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token|password|passwd|client[_-]?secret)\s*[=:]\s*["'][^"'\r\n]{8,}["']''',
}
PRIVATE_DIRS = {'.git', '.venv', '__pycache__', '.aws', '.ssh', 'node_modules'}
PRIVATE_SUFFIXES = ('.db', '.db-wal', '.db-shm', '.sqlite3', '.sqlite3-wal', '.sqlite3-shm',
                    '.log', '.pem', '.key', '.p12', '.pfx')


def findings(path, data, private_terms=()):
    """Return finding categories only; never return matched values."""
    name = PurePosixPath(path).name
    result = []
    if PRIVATE_DIRS.intersection(PurePosixPath(path).parts) or name.endswith(PRIVATE_SUFFIXES):
        result.append('private runtime file')
    if (name == '.env' or name.startswith('.env.')) and name != '.env.example':
        result.append('environment file')
    if name in {'settings.json', 'credentials', 'id_rsa', 'id_ed25519'}:
        result.append('private settings or credential file')
    if name.endswith('.gz'):
        try:
            data = gzip.decompress(data)
        except (OSError, EOFError):
            result.append('unreadable compressed file')
    for category, pattern in PATTERNS.items():
        if re.search(pattern, data):
            result.append(category)
    for term in private_terms:
        if term.encode().lower() in data.lower():
            result.append('private search term')
            break
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive')
    parser.add_argument('--private-term', action='append', default=[])
    args = parser.parse_args()
    problems = []
    with zipfile.ZipFile(args.archive) as source:
        for item in source.infolist():
            if item.is_dir():
                continue
            for category in findings(item.filename, source.read(item), args.private_term):
                problems.append(f'{item.filename}: {category}')
    if problems:
        print('\n'.join(problems))
        raise SystemExit(1)
    print('PASS: publication archive privacy checks. Pattern checks cannot detect every possible secret.')


if __name__ == '__main__':
    main()
