#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2024, NOTO Kazufumi <noto.kazufumi@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: zabbix_api

short_description: Call zabbix api.

description:
    - This module allows you to call Zabbix api.

author:
    - NOTO Kazufumi(@notok)

requirements:
    - "python >= 3.9"

version_added: 3.1.2

options:
    api_method:
        description:
            - API method to call.
        required: true
        type: str
    api_options:
        description:
            - Options for api to be set in request params. (see example below).
        type: dict

notes:
    - This module calls arbitrary zabbix api.

extends_documentation_fragment:
    - community.zabbix.zabbix
"""

EXAMPLES = """
# If you want to use Username and Password to be authenticated by Zabbix Server
- name: Set credentials to access Zabbix Server API
  ansible.builtin.set_fact:
    ansible_user: Admin
    ansible_httpapi_pass: zabbix

# If you want to use API token to be authenticated by Zabbix Server
# https://www.zabbix.com/documentation/current/en/manual/web_interface/frontend_sections/administration/general#api-tokens
- name: Set API token
  ansible.builtin.set_fact:
    ansible_zabbix_auth_key: 8ec0d52432c15c91fcafe9888500cf9a607f44091ab554dbee860f6b44fac895

# Example scenario: creating scheduled report
- name: Get user info to send report to.
  # set task level variables as we change ansible_connection plugin here
  vars:
    ansible_network_os: community.zabbix.zabbix
    ansible_connection: httpapi
    ansible_httpapi_port: 443
    ansible_httpapi_use_ssl: true
    ansible_httpapi_validate_certs: false
    ansible_zabbix_url_path: "zabbixeu"  # If Zabbix WebUI runs on non-default (zabbix) path ,e.g. http://<FQDN>/zabbixeu
    ansible_host: zabbix-example-fqdn.org
  community.zabbix.zabbix_user_info:
    username: "Admin"
  register: user_info

- name: Get dashboard info to create report with.
  # set task level variables as we change ansible_connection plugin here
  vars:
    ansible_network_os: community.zabbix.zabbix
    ansible_connection: httpapi
    ansible_httpapi_port: 443
    ansible_httpapi_use_ssl: true
    ansible_httpapi_validate_certs: false
    ansible_zabbix_url_path: "zabbixeu"  # If Zabbix WebUI runs on non-default (zabbix) path ,e.g. http://<FQDN>/zabbixeu
    ansible_host: zabbix-example-fqdn.org
  community.zabbix.zabbix_api:
    method: dashboard.get
    params:
      filter:
        name: "Zabbix server health"
  register: dashboard_info

- name: Create report.
  # set task level variables as we change ansible_connection plugin here
  vars:
    ansible_network_os: community.zabbix.zabbix
    ansible_connection: httpapi
    ansible_httpapi_port: 443
    ansible_httpapi_use_ssl: true
    ansible_httpapi_validate_certs: false
    ansible_zabbix_url_path: "zabbixeu"  # If Zabbix WebUI runs on non-default (zabbix) path ,e.g. http://<FQDN>/zabbixeu
    ansible_host: zabbix-example-fqdn.org
  community.zabbix.zabbix_api:
    method: report.create
    params:
      userid: "{{ user_info.zabbix_user.userid }}"
      name: "Daily report"
      dashboardid: "{{ dashboard_info.result[0].dashboardid }}"
      start_time: "43200"
      subject: "Daily report"
      message: "Report from zabbix"
      description: "Report description"
      users:
        userid: "{{ user_info.zabbix_user.userid }}"
"""

RETURN = """
result:
    description: The result of the operation depends on executed method
    returned: success
    type: complex
    sample: { "reportids": ["2"] }
"""

import re

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.zabbix.plugins.module_utils.base import ZabbixBase
import ansible_collections.community.zabbix.plugins.module_utils.helpers as zabbix_utils


class API(ZabbixBase):
    def _is_method(self, method):
        pattern = re.compile(r"^[a-z]+\.[a-z]+$")
        search_result = pattern.search(method)
        if search_result is None:
            self._module.fail_json(msg="{0} is invalid value.".format(method))
        return True

    def call(
        self,
        method,
        params={},
    ):
        try:
            if isinstance(method, str):
                if self._is_method(method):
                    target_object, target_method = method.split(".")

            if self._module.check_mode:
                self._module.exit_json(changed=True)

            apireq = getattr(self._zapi, target_object)
            apimethod = getattr(apireq, target_method)
            res = apimethod(params)

            self._module.exit_json(changed=True, result=res)
        except Exception as e:
            self._module.fail_json(msg="Failed to call api: %s" % e)


def main():
    argument_spec = zabbix_utils.zabbix_common_argument_spec()
    argument_spec.update(
        dict(
            method=dict(type="str", required=True),
            params=dict(type="dict", required=False),
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    method = module.params["method"]
    params = module.params["params"]

    api = API(module)
    api.call(
        method,
        params,
    )


if __name__ == "__main__":
    main()
