# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from unittest.mock import patch

import pytest

import wca.security


@patch('wca.security._read_paranoid')
@patch('wca.security.LIBC.capget', return_value=-1)
def test_privileges_failed_capget(capget, read_paranoid):
    with pytest.raises(wca.security.GettingCapabilitiesFailed):
        wca.security.are_privileges_sufficient(True)


def no_cap_dac_override_no_cap_setuid(header, data):
    # https://github.com/python/cpython/blob/v3.6.6/Modules/_ctypes/callproc.c#L521
    # Do not even ask how I managed to find it ;)
    data._obj.effective = 20  # 20 & 128 = 0, 20 & 2 = 0
    return 0


def cap_dac_override_cap_setuid(header, data):
    # https://github.com/python/cpython/blob/v3.6.6/Modules/_ctypes/callproc.c#L521
    data._obj.effective = 2 + 128  # 130 & 128 = 128, 130 & 2 = 2
    return 0


def no_cap_dac_override_cap_setuid(header, data):
    # https://github.com/python/cpython/blob/v3.6.6/Modules/_ctypes/callproc.c#L521
    data._obj.effective = 1 + 128  # 130 & 128 = 128, 129 & 2 = 2
    return 0


def cap_dac_override_no_cap_setuid(header, data):
    # https://github.com/python/cpython/blob/v3.6.6/Modules/_ctypes/callproc.c#L521
    data._obj.effective = 2 + 1  # 3 & 128 = 0, 3 & 2 = 2
    return 0


@patch('os.geteuid', return_value=0)
@patch('wca.security._read_paranoid', return_value=2)
@patch('wca.security.LIBC.capget', side_effect=no_cap_dac_override_no_cap_setuid)
def test_privileges_root_no_dac_no_paranoid_no_setuid(capget, read_paranoid, geteuid):
    assert wca.security.are_privileges_sufficient(True)


@patch('os.geteuid', return_value=1000)
@patch('wca.security._read_paranoid', return_value=2)
@patch('wca.security.LIBC.capget', side_effect=cap_dac_override_cap_setuid)
def test_privileges_not_root_no_dac_paranoid_cap_setuid(capget, read_paranoid, geteuid):
    assert not wca.security.are_privileges_sufficient(True)


@patch('os.geteuid', return_value=1000)
@patch('wca.security._read_paranoid', return_value=0)
@patch('wca.security.LIBC.capget', side_effect=no_cap_dac_override_no_cap_setuid)
def test_privileges_not_root_no_capabilities_no_dac_paranoid_no_setuid(capget,
                                                                       read_paranoid,
                                                                       geteuid):
    assert not wca.security.are_privileges_sufficient(True)


@patch('os.geteuid', return_value=1000)
@patch('wca.security._read_paranoid', return_value=0)
@patch('wca.security.LIBC.capget', side_effect=cap_dac_override_cap_setuid)
def test_privileges_not_root_capabilities_dac_paranoid_setuid(capget, read_paranoid, geteuid):
    assert wca.security.are_privileges_sufficient(True)


@patch('os.geteuid', return_value=1000)
@patch('wca.security._read_paranoid', return_value=0)
@patch('wca.security.LIBC.capget', side_effect=cap_dac_override_no_cap_setuid)
def test_privileges_not_root_capabilities_dac_paranoid_no_setuid(capget, read_paranoid, geteuid):
    assert not wca.security.are_privileges_sufficient(True)


@patch('os.geteuid', return_value=1000)
@patch('wca.security._read_paranoid', return_value=0)
@patch('wca.security.LIBC.capget', side_effect=no_cap_dac_override_cap_setuid)
def test_privileges_not_root_capabilities_no_dac_paranoid_setuid(capget, read_paranoid, geteuid):
    assert not wca.security.are_privileges_sufficient(True)


@patch('os.path.isfile', return_value=False)
def test_sslcert_available_files(mock_isfile):
    with pytest.raises(FileNotFoundError):
        wca.security.SSLCert('cert', 'key')


@patch('os.path.isfile', return_value=True)
@patch('os.access', return_value=False)
def test_sslcert_permmision_for_files(mock_access, mock_isfile):
    with pytest.raises(PermissionError):
        wca.security.SSLCert('cert', 'key')
