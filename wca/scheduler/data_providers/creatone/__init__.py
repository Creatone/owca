# Copyright (c) 2020 Intel Corporation
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
from abc import abstractmethod
from enum import Enum
from typing import Dict

from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import AppName, NodeName


class NodeType(str, Enum):
    PMEM = 'pmem'
    DRAM = 'dram'
    UNKNOWN = 'unknown'

    def __repr__(self):
        return self.value


class CreatoneDataProvider(DataProvider):
    @abstractmethod
    def get_app_profiles(self, profile_query: str) -> Dict[AppName, float]:
        pass

    @abstractmethod
    def get_nodes_profiles(self) -> Dict[NodeName, NodeType]:
        pass
