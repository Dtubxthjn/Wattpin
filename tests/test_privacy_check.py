from tools.privacy_check import findings


def test_publication_rejects_credentials_without_echoing_them():
    token = b'ghp_' + b'A' * 36
    result = findings('source.py', b'token = ' + token)
    assert result == ['GitHub token']
    assert not any(token.decode() in entry for entry in result)
    assert 'private key' in findings('key.txt', b'-----BEGIN ' + b'PRIVATE KEY-----')
    assert 'credentialed URL' in findings('url.txt', b'https://' + b'user:password@example.com')


def test_publication_rejects_runtime_data_and_private_paths():
    for path in ['.env', '.env.production', 'settings.json', 'sessions.sqlite3', 'sessions.sqlite3-shm', '.aws/config']:
        assert findings(path, b'')
    assert 'personal home path' in findings('source.py', b'/home/' + b'someone/private')
    assert 'private search term' in findings('note.txt', b'private-marker', ['private-marker'])


def test_publication_allows_templates_and_public_source():
    assert findings('.env.example', b'') == []
    assert findings('README.md', b'https://github.com/example/project') == []
    assert findings('licenses/LICENSE', b'Copyright upstream <maintainer@example.com>') == []
