from functools import partial as p
import os
import pytest
import string

from tests.helpers.util import wait_for, run_agent
from tests.helpers.assertions import *
from tests.kubernetes.utils import (
    run_k8s_monitors_test,
    get_metrics_from_doc,
    get_dims_from_doc,
)

pytestmark = [pytest.mark.collectd, pytest.mark.custom, pytest.mark.custom_collectd, pytest.mark.monitor_without_endpoints]


def test_custom_collectd():
    with run_agent("""
monitors:
  - type: collectd/df
  - type: collectd/custom
    template: |
      LoadPlugin "ping"
      <Plugin ping>
        Host "google.com"
      </Plugin>
""") as [backend, _, _]:
        assert wait_for(p(has_datapoint_with_dim, backend, "plugin", "ping")), "Didn't get ping datapoints"
        assert wait_for(p(has_datapoint_with_dim, backend, "plugin", "df")), "Didn't get df datapoints"


def test_custom_collectd_multiple_templates():
    with run_agent("""
monitors:
  - type: collectd/df
  - type: collectd/custom
    templates:
     - |
       LoadPlugin "cpu"
     - |
       LoadPlugin "ping"
       <Plugin ping>
         Host "google.com"
       </Plugin>
collectd:
  logLevel: debug
""") as [backend, _, _]:
        assert wait_for(p(has_datapoint_with_dim, backend, "plugin", "df")), "Didn't get df datapoints"
        assert wait_for(p(has_datapoint_with_dim, backend, "plugin", "cpu")), "Didn't get cpu datapoints"
        assert wait_for(p(has_datapoint_with_dim, backend, "plugin", "ping")), "Didn't get ping datapoints"


@pytest.mark.k8s
@pytest.mark.kubernetes
def test_custom_collectd_in_k8s(agent_image, minikube, k8s_test_timeout):
    monitors = [
        {"type": "collectd/custom",
         "templates": [
            '''LoadPlugin "cpu"''',
            '''LoadPlugin "ping"
               <Plugin ping>
                 Host "google.com"
               </Plugin>'''
         ]},
        {"type": "collectd/signalfx-metadata"},
        {"type": "collectd/df"}
    ]
    run_k8s_monitors_test(
        agent_image,
        minikube,
        monitors,
        expected_metrics=get_metrics_from_doc("collectd-cpu.md").union(get_metrics_from_doc("collectd-df.md")),
        expected_dims=get_dims_from_doc("collectd-cpu.md").union(get_dims_from_doc("collectd-df.md")),
        test_timeout=k8s_test_timeout)

