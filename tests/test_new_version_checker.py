from requests_mock import Mocker
from time import sleep
from unittest import TestCase
from mock import Mock, MagicMock, patch
from ddt import ddt, data, unpack
from monitorrent.new_version_checker import NewVersionChecker
from tests import use_vcr, ReadContentMixin


@ddt
class NewVersionCheckerTest(TestCase, ReadContentMixin):
    @use_vcr()
    def test_get_latest_public_release(self):
        checker = NewVersionChecker(Mock(), False)

        self.assertEqual('1.0.2', checker.get_latest_release())

    @use_vcr()
    def test_get_latest_prerelease_release(self):
        checker = NewVersionChecker(Mock(), True)

        self.assertEqual('1.1.0-rc.1.1', checker.get_latest_release())

    @Mocker()
    def test_get_latest_release_with_error_tag_success(self, mocker):
        """
        :type mocker: Mocker
        """
        checker = NewVersionChecker(Mock(), True)

        mocker.get('https://api.github.com/repos/werwolfby/monitorrent/releases',
                   text=self.read_httpretty_content('github.com_releases.json', encoding='utf-8'))
        self.assertEqual('1.1.0-rc.4', checker.get_latest_release())

    @use_vcr()
    @data('0.0.3-alpha', '1.0.0', '1.0.1')
    def test_new_public_version_url(self, version):
        notifier_manager_execute = MagicMock()
        notifier_manager_execute.notify = Mock()
        notifier_manager_execute.__enter__ = Mock(return_value=notifier_manager_execute)

        notifier_manager = Mock()
        notifier_manager.execute = Mock(name="notifier_manager.execute123", return_value=notifier_manager_execute)
        checker = NewVersionChecker(notifier_manager, False)

        with patch('monitorrent.new_version_checker.monitorrent', create=True) as version_mock:
            version_mock.__version__ = version

            checker.execute()

            self.assertEqual('https://github.com/werwolfby/monitorrent/releases/tag/1.0.2', checker.new_version_url)
            notifier_manager_execute.notify.assert_called_once()

    @use_vcr()
    def test_new_public_version_url_and_faile_notify_should_not_fail_execute(self):
        notifier_manager_execute = MagicMock()
        notifier_manager_execute.notify = Mock(side_effect=Exception)
        notifier_manager_execute.__enter__ = Mock(return_value=notifier_manager_execute)

        notifier_manager = Mock()
        notifier_manager.execute = Mock(name="notifier_manager.execute123", return_value=notifier_manager_execute)
        checker = NewVersionChecker(notifier_manager, False)

        with patch('monitorrent.new_version_checker.monitorrent', create=True) as version_mock:
            version_mock.__version__ = "0.0.3-alpha"

            checker.execute()

            self.assertEqual('https://github.com/werwolfby/monitorrent/releases/tag/1.0.2', checker.new_version_url)
            notifier_manager_execute.notify.assert_called_once()

    def test_timer_calls(self):
        checker = NewVersionChecker(Mock(), False)

        execute_mock = Mock(return_value=True)
        checker.execute = execute_mock

        checker.start(0.1)
        sleep(0.3)
        checker.stop()

        self.assertGreaterEqual(execute_mock.call_count, 2)
        self.assertLess(execute_mock.call_count, 4)

        sleep(0.3)

        self.assertLess(execute_mock.call_count, 4)

    def test_timer_stop_dont_call_execute(self):
        checker = NewVersionChecker(Mock(), False)

        execute_mock = Mock(return_value=True)
        checker.execute = execute_mock

        checker.start(1)
        checker.stop()

        execute_mock.assert_not_called()

        self.assertLess(execute_mock.call_count, 4)

    def test_start_twice_should_raise(self):
        checker = NewVersionChecker(Mock(), False)

        execute_mock = Mock(return_value=True)
        checker.execute = execute_mock

        checker.start(10)
        with self.assertRaises(Exception):
            checker.start(10)
        checker.stop()

        execute_mock.assert_not_called()

    def test_is_started(self):
        checker = NewVersionChecker(Mock(), False)

        execute_mock = Mock(return_value=True)
        checker.execute = execute_mock

        checker.start(10)
        self.assertTrue(checker.is_started())
        checker.stop()
        self.assertFalse(checker.is_started())

        execute_mock.assert_not_called()

    @data(
        (True, True, 3600, False, 7200, False, True),
        (False, True, 3600, False, 7200, False, True),
        (True, True, 3600, False, 7200, False, True),
        (False, True, 3600, False, 7200, False, True),
        (True, True, 3600, True, 3600, False, False),
        (False, True, 3600, True, 3600, False, False),
        (True, True, 3600, True, 7200, True, True),
        (False, True, 3600, True, 7200, True, True),
        (True, False, 3600, True, 3600, True, False),
        (False, False, 3600, True, 3600, True, False),
        (True, False, 3600, True, 7200, True, False),
        (False, False, 3600, True, 7200, True, False),
        (True, False, 3600, False, 3600, False, False),
        (False, False, 3600, False, 3600, False, False),
        (True, False, 3600, False, 7200, False, False),
        (False, False, 3600, False, 7200, False, False),
    )
    @unpack
    def test_update(self, include_prerelease, is_started, start_interval, enabled, interval, start_called, stop_called):
        checker = NewVersionChecker(Mock(), False)

        def start_side_effect(i):
            checker.interval = i

        start_mock = Mock(side_effect=start_side_effect)
        stop_mock = Mock()
        is_started_mock = Mock(return_value=is_started)

        checker.interval = start_interval
        checker.start = start_mock
        checker.stop = stop_mock
        checker.is_started = is_started_mock

        checker.update(include_prerelease, enabled, interval)

        self.assertEqual(checker.interval, interval)
        self.assertEqual(checker.include_prereleases, include_prerelease)
        if start_called:
            start_mock.assert_called_once_with(interval)
        else:
            start_mock.assert_not_called()

        if stop_called:
            stop_mock.assert_called_once()
        else:
            stop_mock.assert_not_called()
