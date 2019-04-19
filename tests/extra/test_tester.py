# Copyright (c) 2019 Intel Corporation
# # Licensed under the Apache License, Version 2.0 (the "License"); # you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from unittest.mock import MagicMock, Mock, patch

from owca.extra.tester import Tester
from owca.nodes import Task


@patch('owca.extra.tester._create_cgroup')
def test_tester(create_cgroup_mock: MagicMock):
    tester = Tester('tests/extra/tester_config.yaml')
    tester._clean_tasks = MagicMock(return_value=None)
    

    # Firstly only prepare cgroups ( and processess ) and return tasks from config.
    assert tester.get_tasks() == [Task(
        name='task1', task_id='task1', cgroup_path='/test/task1',
        labels={}, resources={}, subcgroups_paths=[]), Task(
            name='task2', task_id='task2', cgroup_path='/test/task2',
            labels={}, resources={}, subcgroups_paths=[])]

    assert tester._clean_tasks.called

    # Secondly do previous checks.
    assert tester.get_tasks() == [Task(
        name='task1', task_id='task1', cgroup_path='/test/task1',
        labels={}, resources={}, subcgroups_paths=[]), Task(
            name='task2', task_id='task2', cgroup_path='/test/task2',
            labels={}, resources={}, subcgroups_paths=[])]
