from concurrent.futures import ThreadPoolExecutor
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
