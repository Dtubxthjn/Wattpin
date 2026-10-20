from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from powerglass import ipc
from powerglass.ipc import send_request


def test_concurrent_requests_have_no_shared_temporary_file(tmp_path):
    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(lambda _:send_request(tmp_path,'show'),range(100)))
    assert (tmp_path/'show-request').read_text()=='show'
    assert not list(tmp_path.glob('.request-*'))


def test_shutdown_request_replaces_a_pending_show_request(tmp_path):
    send_request(tmp_path,'show')
    send_request(tmp_path,'quit')
    assert (tmp_path/'show-request').read_text()=='quit'


@pytest.mark.parametrize('winerror', [5, 32, 33])
def test_windows_busy_request_is_retried(tmp_path, monkeypatch, winerror):
    replace = Path.replace
    calls = []

    def busy_then_replace(path, target):
        calls.append(target)
        if len(calls) < 4:
            error = PermissionError('request is busy')
            error.winerror = winerror
            raise error
        return replace(path, target)

    monkeypatch.setattr(Path, 'replace', busy_then_replace)
    monkeypatch.setattr(ipc.time, 'sleep', lambda _: None)
    send_request(tmp_path, 'quit')
    assert len(calls) == 4
    assert (tmp_path / 'show-request').read_text() == 'quit'
    assert not list(tmp_path.glob('.request-*'))


@pytest.mark.parametrize('winerror, attempts', [(5, 40), (None, 1)])
def test_request_errors_are_bounded_and_cleaned_up(tmp_path, monkeypatch,
                                                winerror, attempts):
    calls = []
    error = PermissionError('access denied')
    if winerror is not None:
        error.winerror = winerror

    def denied(path, target):
        calls.append(target)
        raise error

    monkeypatch.setattr(Path, 'replace', denied)
    monkeypatch.setattr(ipc.time, 'sleep', lambda _: None)
    with pytest.raises(PermissionError):
        send_request(tmp_path, 'show')
    assert len(calls) == attempts
    assert not list(tmp_path.glob('.request-*'))
