from functools import partial as p
import os
import pytest
import string

from tests.helpers.util import wait_for, run_agent, run_service
from tests.helpers.assertions import *
from tests.kubernetes.utils import (
    run_k8s_monitors_test,
    get_metrics_from_doc,
    get_dims_from_doc,
)

pytestmark = [pytest.mark.collectd, pytest.mark.nginx, pytest.mark.monitor_with_endpoints]

nginx_config = string.Template("""
monitors:
  - type: collectd/nginx
    host: $host
    port: 80
""")


def test_nginx():
    with run_service("nginx") as nginx_container:
        config = nginx_config.substitute(host=nginx_container.attrs["NetworkSettings"]["IPAddress"])

        with run_agent(config) as [backend, _, _]:
            assert wait_for(p(has_datapoint_with_dim, backend, "plugin", "nginx")), "Didn't get nginx datapoints"


@pytest.mark.k8s
@pytest.mark.kubernetes
def test_nginx_in_k8s(agent_image, minikube, k8s_observer, k8s_test_timeout):
    monitors = [
        {"type": "collectd/nginx",
         "discoveryRule": 'container_image =~ "nginx" && private_port == 80',
         "url": 'http://{{.Host}}:{{.Port}}/nginx_status',
         "username": "testuser", "password": "testing123"},
    ]
    yamls = [os.path.join(os.path.dirname(os.path.realpath(__file__)), y) for y in ["nginx-configmap.yaml", "nginx.yaml"]]
    run_k8s_monitors_test(
        agent_image,
        minikube,
        monitors,
        yamls=yamls,
        observer=k8s_observer,
        expected_metrics=get_metrics_from_doc("collectd-nginx.md"),
        expected_dims=get_dims_from_doc("collectd-nginx.md"),
        test_timeout=k8s_test_timeout)

