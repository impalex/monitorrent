import falcon
import six
from monitorrent.settings_manager import SettingsManager
from monitorrent.new_version_checker import NewVersionChecker


# noinspection PyUnusedLocal
class SettingsNewVersionChecker(object):
    def __init__(self, settings_manager, new_version_checker):
        """
        :type settings_manager: SettingsManager
        :type new_version_checker: NewVersionChecker
        """
        self.settings_manager = settings_manager
        self.new_version_checker = new_version_checker

    def on_get(self, req, resp):
        resp.json = {
            'include_prerelease': self.settings_manager.get_new_version_check_include_prerelease(),
            'enabled': self.settings_manager.get_is_new_version_checker_enabled(),
            'interval': self.settings_manager.new_version_check_interval
        }

    def on_patch(self, req, resp):
        if req.json is None or len(req.json) == 0:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        include_prerelease = req.json.get('include_prerelease')
        if include_prerelease is not None and not isinstance(include_prerelease, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"include_prerelease" have to be bool')

        enabled = req.json.get('enabled')
        if enabled is not None and not isinstance(enabled, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"enabled" have to be bool')

        check_interval = req.json.get('interval')
        if check_interval is not None and not isinstance(check_interval, int):
            raise falcon.HTTPBadRequest('WrongValue', '"interval" have to be int')

        if include_prerelease is not None:
            if self.settings_manager.get_new_version_check_include_prerelease() != include_prerelease:
                self.settings_manager.set_new_version_check_include_prerelease(include_prerelease)
        else:
            include_prerelease = self.settings_manager.get_new_version_check_include_prerelease()

        if enabled is not None:
            if self.settings_manager.get_is_new_version_checker_enabled() != enabled:
                self.settings_manager.set_is_new_version_checker_enabled(enabled)
        else:
            enabled = self.settings_manager.get_is_new_version_checker_enabled()

        if check_interval is not None:
            if self.settings_manager.new_version_check_interval != check_interval:
                self.settings_manager.new_version_check_interval = check_interval
        else:
            check_interval = self.settings_manager.new_version_check_interval

        self.new_version_checker.update(include_prerelease, enabled, check_interval)

        resp.status = falcon.HTTP_NO_CONTENT
