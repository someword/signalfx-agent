from functools import partial as p
from kubernetes import client as kube_client
from tests.helpers.assertions import *
from tests.helpers.util import *
import os
import netifaces as ni
import re
import time

AGENT_YAMLS_DIR = os.environ.get("AGENT_YAMLS_DIR", "/go/src/github.com/signalfx/signalfx-agent/deployments/k8s")
AGENT_CONFIGMAP_PATH = os.environ.get("AGENT_CONFIGMAP_PATH", os.path.join(AGENT_YAMLS_DIR, "configmap.yaml"))
AGENT_DAEMONSET_PATH = os.environ.get("AGENT_DAEMONSET_PATH", os.path.join(AGENT_YAMLS_DIR, "daemonset.yaml"))
AGENT_SERVICEACCOUNT_PATH = os.environ.get("AGENT_SERVICEACCOUNT_PATH", os.path.join(AGENT_YAMLS_DIR, "serviceaccount.yaml"))
DOCS_DIR = os.environ.get("DOCS_DIR", "/go/src/github.com/signalfx/signalfx-agent/docs")
MONITORS_DOCS_DIR = os.path.join(DOCS_DIR, "monitors")
OBSERVERS_DOCS_DIR = os.path.join(DOCS_DIR, "observers")
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
K8S_CREATE_TIMEOUT = 120
K8S_DELETE_TIMEOUT = 10


def run_k8s_monitors_test(agent_image, minikube, monitors, observer="k8s-api", yamls=[], yamls_timeout=K8S_CREATE_TIMEOUT, expected_metrics=set(), expected_dims=set(), test_timeout=60):
    if expected_dims is not None:
        observer_doc = os.path.join(OBSERVERS_DOCS_DIR, observer + ".md")
        expected_dims = expected_dims.union(get_dims_from_doc(observer_doc), {"kubernetes_cluster"})
    if expected_metrics and len(expected_metrics) == 0:
        metrics_txt = os.path.join(CUR_DIR, monitors[0]["type"].replace("/", "-") + '-metrics.txt')
        if os.path.isfile(metrics_txt):
            with open(metrics_txt, "r") as fd:
                expected_metrics = {m.strip() for m in fd.readlines() if len(m.strip()) > 0}
    with fake_backend.start(ip=get_host_ip()) as backend:
        with minikube.deploy_k8s_yamls(yamls, timeout=yamls_timeout):
            with minikube.deploy_agent(
                AGENT_CONFIGMAP_PATH,
                AGENT_DAEMONSET_PATH,
                AGENT_SERVICEACCOUNT_PATH,
                observer=observer,
                monitors=monitors,
                cluster_name="minikube",
                backend=backend,
                image_name=agent_image["name"],
                image_tag=agent_image["tag"],
                namespace="default") as agent:
                if "collectd/statsd" in [m["type"] for m in monitors]:
                    # hack to populate data for statsd
                    agent.container.exec_run(["/bin/bash", "-c", 'while true; do echo "statsd.[foo=bar,dim=val]test:1|g" | nc -w 1 -u 127.0.0.1 8125; sleep 1; done'], detach=True)
                if expected_metrics and expected_dims:
                    print("\nTesting for any of %d metric(s) with any of %d dimension key(s) ..." % (len(expected_metrics), len(expected_dims)))
                    assert wait_for(p(any_metric_has_any_dim_key, backend, expected_metrics, expected_dims), timeout_seconds=test_timeout), \
                        "timed out waiting for any metric in %s with any dimension key in %s!\n\nAGENT STATUS:\n%s\n\nAGENT CONTAINER LOGS:\n%s\n" % \
                        (expected_metrics, expected_dims, agent.get_status(), agent.get_container_logs())
                elif expected_metrics:
                    print("\nTesting for any of %d metric(s) ..." % len(expected_metrics))
                    assert wait_for(p(any_metric_found, backend, expected_metrics), timeout_seconds=test_timeout), \
                        "timed out waiting for any metric in %s!\n\nAGENT STATUS:\n%s\n\nAGENT CONTAINER LOGS:\n%s\n" % \
                        (expected_metrics, agent.get_status(), agent.get_container_logs())
                elif expected_dims:
                    print("\nTesting for any of %d dimension key(s) ..." % len(expected_dims))
                    assert wait_for(p(any_dim_key_found, backend, expected_dims), timeout_seconds=test_timeout), \
                        "timed out waiting for any dimension key in %s!\n\nAGENT STATUS:\n%s\n\nAGENT CONTAINER LOGS:\n%s\n" % \
                        (expected_dims, agent.get_status(), agent.get_container_logs())
                agent_status = agent.get_status()
                container_logs = agent.get_container_logs()
                assert "testing123" not in agent_status, "plaintext password(s) found in agent-status output!\n\n%s\n" % agent_status
                assert "testing123" not in container_logs, "plaintext password(s) found in agent container logs!\n\n%s\n" % container_logs


def get_metrics_from_doc(doc, ignore=[], doc_dir=MONITORS_DOCS_DIR):
    """
    Parse markdown document for metrics.

    Args:
    doc (str):            Name or path to markdown document
    ignore (list of str): Metrics to exclude/ignore
    doc_dir (str):        Directory containing `doc`

    Returns:
    Sorted set of metric names from `doc` excluding those in `ignore`
    """
    if not os.path.isfile(doc) and doc_dir and os.path.isdir(doc_dir):
        doc = os.path.join(doc_dir, doc)
        assert os.path.isfile(doc), "\"%s\" not found!" % doc
    else:
        assert os.path.isfile(doc), "\"%s\" not found!" % doc
    with open(doc, 'r') as fd:
        metrics = set(re.findall('\|\s+`(.*?)`\s+\|\s+(?:counter|gauge|cumulative)\s+\|', fd.read(), re.IGNORECASE))
        if len(metrics) > 0 and len(ignore) > 0:
            metrics.difference_update(set(ignore))
        return set(sorted(metrics))


# returns a sorted set of dimension names from `doc` excluding those in `ignore`
def get_dims_from_doc(doc, ignore=[], doc_dir=MONITORS_DOCS_DIR):
    """
    Parse markdown document for dimensions.

    Args:
    doc (str):            Name or path to markdown document
    ignore (list of str): Metrics to exclude/ignore
    doc_dir (str):        Directory containing `doc`

    Returns:
    Sorted set of dimensions from `doc` excluding those in `ignore`
    """
    if not os.path.isfile(doc) and doc_dir and os.path.isdir(doc_dir):
        doc = os.path.join(doc_dir, doc)
        assert os.path.isfile(doc), "\"%s\" not found!" % doc
    else:
        assert os.path.isfile(doc), "\"%s\" not found!" % doc
    with open(doc, 'r') as fd:
        dims = set()
        line = fd.readline()
        while line and not re.match('\s*##\s*Dimensions.*', line):
            line = fd.readline()
        if line:
            dim_line = re.compile('\|\s+`(.*?)`\s+\|.*\|')
            match = None
            while line and not match:
                line = fd.readline()
                match = dim_line.match(line)
            while line and match:
                dims.add(match.group(1))
                line = fd.readline()
                match = dim_line.match(line)
        if len(dims) > 0 and len(ignore) > 0:
            dims.differnce_update(set(ignore))
        return set(sorted(dims))


def get_host_ip():
    gws = ni.gateways()
    interface = gws['default'][ni.AF_INET][1]
    return ni.ifaddresses(interface)[ni.AF_INET][0]['addr']


def has_secret(name, namespace="default"):
    api = kube_client.CoreV1Api()
    try:
        api.read_namespaced_secret(name, namespace=namespace)
        return True
    except:
        return False


def create_secret(name, key, value, namespace="default"):
    api = kube_client.CoreV1Api()
    return api.create_namespaced_secret(
        body=kube_client.V1Secret(
            metadata=kube_client.V1ObjectMeta(name=name),
            string_data={key: value}),
        namespace=namespace)


def has_serviceaccount(name, namespace="default"):
    api = kube_client.CoreV1Api()
    try:
        api.read_namespaced_service_account(name, namespace=namespace)
        return True
    except:
        return False


def create_serviceaccount(body=None, namespace="default", timeout=K8S_CREATE_TIMEOUT):
    api = kube_client.CoreV1Api()
    if body:
        name = body['metadata']['name']
        body["apiVersion"] = "v1"
        try:
            namespace = body["metadata"]["namespace"]
        except:
            pass
    serviceaccount = api.create_namespaced_service_account(
        body=body,
        namespace=namespace)
    assert wait_for(p(has_serviceaccount, name, namespace=namespace), timeout_seconds=timeout), "timed out waiting for service account \"%s\" to be created!" % name
    return serviceaccount


def has_configmap(name, namespace="default"):
    api = kube_client.CoreV1Api()
    try:
        api.read_namespaced_config_map(name, namespace=namespace)
        return True
    except:
        return False


def create_configmap(body=None, name="", data={}, labels={}, namespace="default", timeout=K8S_CREATE_TIMEOUT):
    api = kube_client.CoreV1Api()
    if body:
        name = body['metadata']['name']
        body["apiVersion"] = "v1"
        try:
            namespace = body["metadata"]["namespace"]
        except:
            pass
    else:
        body = kube_client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=kube_client.V1ObjectMeta(name=name, labels=labels),
            data=data)
    configmap = api.create_namespaced_config_map(
        body=body,
        namespace=namespace)
    assert wait_for(p(has_configmap, name, namespace=namespace), timeout_seconds=timeout), "timed out waiting for configmap \"%s\" to be created!" % name
    return configmap


def patch_configmap(body, namespace="default", timeout=K8S_CREATE_TIMEOUT):
    api = kube_client.CoreV1Api()
    name = body['metadata']['name']
    body["apiVersion"] = "v1"
    try:
        namespace = body["metadata"]["namespace"]
    except:
        pass
    configmap =  api.patch_namespaced_config_map(
        name=name,
        body=body,
        namespace=namespace)
    assert wait_for(p(has_configmap, name, namespace=namespace), timeout_seconds=timeout), "timed out waiting for configmap \"%s\" to be patched!" % name
    return configmap


def delete_configmap(name, namespace="default", timeout=K8S_DELETE_TIMEOUT):
    if not has_configmap(name, namespace=namespace):
        return
    api = kube_client.CoreV1Api()
    api.delete_namespaced_config_map(
        name=name,
        body=kube_client.V1DeleteOptions(grace_period_seconds=0, propagation_policy='Background'),
        namespace=namespace)
    assert wait_for(lambda: not has_configmap(name, namespace=namespace), timeout), "timed out waiting for configmap \"%s\" to be deleted!" % name


def has_deployment(name, namespace="default"):
    api = kube_client.ExtensionsV1beta1Api()
    try:
        api.read_namespaced_deployment(name, namespace=namespace)
        return True
    except:
        return False


def deployment_is_ready(name, replicas, namespace):
    api = kube_client.ExtensionsV1beta1Api()
    if not has_deployment(name, namespace=namespace):
        return False
    if api.read_namespaced_deployment_status(name, namespace=namespace).status.ready_replicas == replicas:
        return True
    return False


def create_deployment(body=None, name="", pod_template=None, replicas=1, labels={}, namespace="default", timeout=K8S_CREATE_TIMEOUT):
    api = kube_client.ExtensionsV1beta1Api()
    if body:
        name = body["metadata"]["name"]
        body["apiVersion"] = "extensions/v1beta1"
        try:
            namespace = body["metadata"]["namespace"]
        except:
            pass
        try:
            replicas = body["spec"]["replicas"]
        except:
            pass
    else:
        spec = kube_client.ExtensionsV1beta1DeploymentSpec(
            replicas=replicas,
            template=pod_template)
        body = kube_client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=kube_client.V1ObjectMeta(name=name, labels=labels),
            spec=spec)
    deployment = api.create_namespaced_deployment(
        body=body,
        namespace=namespace)
    assert wait_for(p(deployment_is_ready, name, replicas, namespace=namespace), timeout_seconds=timeout), "timed out waiting for deployment \"%s\" to be ready!" % name
    return deployment


def delete_deployment(name, namespace="default", timeout=K8S_DELETE_TIMEOUT):
    if not has_deployment(name, namespace=namespace):
        return
    api = kube_client.ExtensionsV1beta1Api()
    api.delete_namespaced_deployment(
        name=name,
        body=kube_client.V1DeleteOptions(grace_period_seconds=0, propagation_policy='Background'),
        namespace=namespace)
    assert wait_for(lambda: not has_deployment(name, namespace=namespace), timeout), "timed out waiting for deployment \"%s\" to be deleted!" % name


def has_daemonset(name, namespace="default"):
    api = kube_client.ExtensionsV1beta1Api()
    try:
        api.read_namespaced_daemon_set(name, namespace=namespace)
        return True
    except:
        return False


def daemonset_is_ready(name, namespace):
    api = kube_client.ExtensionsV1beta1Api()
    if not has_daemonset(name, namespace=namespace):
        return False
    if api.read_namespaced_daemon_set_status(name, namespace=namespace).status.number_ready > 0:
        return True
    return False


def create_daemonset(body=None, namespace="default", timeout=K8S_CREATE_TIMEOUT):
    api = kube_client.ExtensionsV1beta1Api()
    if body:
        name = body['metadata']['name']
        body["apiVersion"] = "extensions/v1beta1"
        try:
            namespace = body["metadata"]["namespace"]
        except:
            pass
    daemonset = api.create_namespaced_daemon_set(
        body=body,
        namespace=namespace)
    assert wait_for(p(daemonset_is_ready, name, namespace=namespace), timeout_seconds=timeout), "timed out waiting for daemonset \"%s\" to be ready!" % name
    return daemonset


def delete_daemonset(name, namespace="default", timeout=K8S_DELETE_TIMEOUT):
    if not has_daemonset(name, namespace=namespace):
        return
    api = kube_client.ExtensionsV1beta1Api()
    api.delete_namespaced_daemon_set(
        name=name,
        body=kube_client.V1DeleteOptions(grace_period_seconds=0, propagation_policy='Background'),
        namespace=namespace)
    assert wait_for(lambda: not has_daemonset(name, namespace=namespace), timeout), "timed out waiting for daemonset \"%s\" to be deleted!" % name


def get_all_pods():
    """
    Returns:
    List of all pods in the cluster
    """
    v1 = kube_client.CoreV1Api()
    pods = v1.list_pod_for_all_namespaces(watch=False)
    return pods.items


def get_all_pods_matching_name(name):
    """
    Args:
    name (str or regex): Name of pod(s) to search for

    Returns:
    List of all pods in the cluster that matches `name`
    """
    pods = []
    for pod in get_all_pods():
        if re.match(name, pod.metadata.name):
            pods.append(pod)
    return pods


def has_pod(name):
    """
    Args:
    name (str): Name of pod(s) to search for

    Returns:
    True if any pod contains `pod_name`; otherwise False
    """
    for pod in get_all_pods():
        if name in pod.metadata.name:
            return True
    return False


def all_pods_have_ips():
    """
    Returns:
    True if all pods have IPs; otherwise False
    """
    pods = get_all_pods()
    if len(pods) == 0:
        return False
    ips = 0
    for pod in pods:
        if not pod.status.pod_ip:
            return False
        else:
            ips += 1
    if ips == len(pods):
        return True
    return False


def get_all_logs(minikube):
    """
    Args:
    minikube (Minikube): Minikube instance

    Returns:
    String containing:
    - the output from 'agent-status'
    - the agent container logs
    - the output from 'minikube logs'
    - the minikube container logs
    - the status of all pods
    """
    try:
        agent_status = minikube.agent.get_status()
    except:
        agent_status = ""
    try:
        agent_container_logs = minikube.agent.get_container_logs()
    except:
        agent_container_logs = ""
    try:
        _, output = minikube.container.exec_run("minikube logs")
        minikube_logs = output.decode('utf-8').strip()
    except:
        minikube_logs = ""
    try:
        minikube_container_logs = minikube.get_container_logs()
    except:
        minikube_container_logs = ""
    try:
        pods_status = ""
        for pod in get_all_pods():
            pods_status += "%s\t%s\t%s\n" % (pod.status.pod_ip, pod.metadata.namespace, pod.metadata.name)
        pods_status = pods_status.strip()
    except:
        pods_status = ""
    return "AGENT STATUS:\n%s\n\nAGENT CONTAINER LOGS:\n%s\n\nMINIKUBE LOGS:\n%s\n\nMINIKUBE CONTAINER LOGS:\n%s\n\nPODS STATUS:\n%s" % \
        (agent_status, agent_container_logs, minikube_logs, minikube_container_logs, pods_status)
