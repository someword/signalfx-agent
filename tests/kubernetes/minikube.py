from contextlib import contextmanager
from functools import partial as p
from kubernetes import config as kube_config
from tests.helpers.util import *
from tests.kubernetes.agent import Agent
from tests.kubernetes.utils import *
import docker
import os
import time
import yaml

MINIKUBE_VERSION = os.environ.get("MINIKUBE_VERSION", "v0.26.1")
K8S_SERVICES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'services')

class Minikube:
    def __init__(self):
        self.container = None
        self.client = None
        self.version = None
        self.name = None
        self.host_client = get_docker_client()
        self.yamls = []
        self.agent = Agent()
        self.cluster_name = "minikube"
        self.kubeconfig = None
        self.namespace = "default"
        self.ip = None

    def get_client(self):
        if self.container:
            self.client = docker.DockerClient(base_url="tcp://%s:2375" % container_ip(self.container), version='auto')
            return self.client
        else:
            return None

    def get_ip(self):
        if self.container:
            self.ip = container_ip(self.container)
            return self.ip
        else:
            return None

    def load_kubeconfig(self, kubeconfig_path="/kubeconfig", timeout=300):
        assert wait_for(p(container_cmd_exit_0, self.container, "test -f %s" % kubeconfig_path), timeout_seconds=timeout), "timed out waiting for the minikube cluster to be ready!\n\n%s\n\n" % self.container.logs().decode('utf-8').strip()
        self.kubeconfig = "/tmp/scratch/kubeconfig-%s" % self.container.id[:12]
        time.sleep(2)
        rc, output = self.container.exec_run("cp -f %s %s" % (kubeconfig_path, self.kubeconfig))
        assert rc == 0, "failed to get %s from minikube!\n%s" % (kubeconfig_path, output.decode('utf-8'))
        time.sleep(2)
        kube_config.load_kube_config(config_file=self.kubeconfig)

    def connect(self, name, timeout, version=None):
        print("\nConnecting to %s container ..." % name)
        self.container = self.host_client.containers.get(name)
        self.client = self.get_client()
        self.name = name
        self.version = version
        self.load_kubeconfig(timeout=timeout)

    def deploy(self, version, timeout, options={}):
        self.version = version
        if self.version[0] != 'v':
            self.version = 'v' + self.version
        if not options:
            options = {
                "privileged": True,
                "extra_hosts": {
                    "localhost": get_host_ip()
                },
                "environment": {
                    'K8S_VERSION': self.version,
                    'TIMEOUT': str(timeout)
                },
                "ports": {
                    '8080/tcp': None,
                    '8443/tcp': None,
                    '2375/tcp': None,
                },
                "volumes": {
                    "/tmp/scratch": {
                        "bind": "/tmp/scratch",
                        "mode": "rw"
                    },
                }
            }
        print("\nDeploying minikube %s cluster ..." % self.version)
        image, logs = self.host_client.images.build(
            path=os.path.join(TEST_SERVICES_DIR, 'minikube'),
            buildargs={"MINIKUBE_VERSION": MINIKUBE_VERSION},
            tag="minikube:%s" % MINIKUBE_VERSION,
            rm=True,
            forcerm=True)
        self.container = self.host_client.containers.run(
            image.id,
            detach=True,
            **options)
        self.name = self.container.name
        self.load_kubeconfig(timeout=timeout)
        self.container.reload()
        self.get_client()

    @contextmanager
    def deploy_k8s_yamls(self, yamls=[], timeout=120):
        self.yamls = []
        for yaml_file in yamls:
            assert os.path.isfile(yaml_file), "\"%s\" not found!" % yaml_file
            docs = []
            for doc in yaml.load_all(open(yaml_file, "r").read()):
                assert doc['kind'] in ["ConfigMap", "Deployment"], "kind \"%s\" in %s not yet supported!" % (doc['kind'], yaml_file)
                docs.append(doc)
            # create ConfigMaps first
            for doc in docs:
                kind = doc['kind']
                name = doc['metadata']['name']
                namespace = doc['metadata']['namespace']
                if kind == "ConfigMap":
                    if has_configmap(name, namespace=namespace):
                        print("Deleting configmap \"%s\" ..." % name)
                        delete_configmap(name, namespace=namespace)
                    print("Creating configmap from %s ..." % yaml_file)
                    create_configmap(body=doc, timeout=timeout)
                    self.yamls.append(doc)
            # create Deployments
            for doc in docs:
                kind = doc['kind']
                name = doc['metadata']['name']
                namespace = doc['metadata']['namespace']
                if kind == "ConfigMap":
                    continue
                if has_deployment(name, namespace=namespace):
                    print("Deleting deployment \"%s\" ..." % name)
                    delete_deployment(name, namespace=namespace)
                print("Creating deployment from %s ..." % yaml_file)
                create_deployment(body=doc, timeout=timeout)
                self.yamls.append(doc)
        try:
            yield
        finally:
            for y in self.yamls:
                kind = y['kind']
                name = y['metadata']['name']
                namespace = y['metadata']['namespace']
                if kind == "ConfigMap":
                    print("Deleting configmap \"%s\" ..." % name)
                    delete_configmap(name, namespace=namespace)
                elif kind == "Deployment":
                    print("Deleting deployment \"%s\" ..." % name)
                    delete_deployment(name, namespace=namespace)
            self.yamls = []

    def pull_agent_image(self, name, tag="latest"):
        try:
            image_id = self.host_client.images.get("%s:%s" % (name, tag)).id
        except docker.errors.ImageNotFound:
            image_id = None
        assert image_id, "failed to get agent image \"%s:%s\"!" % (name, tag)
        if image_id:
            try:
                self.client.images.get(image_id)
                return
            except docker.errors.ImageNotFound:
                pass
        print("\nPulling %s:%s to the minikube container ..." % (name, tag))
        self.client.images.pull(name, tag=tag)
        _, output = self.container.exec_run('docker images')
        print(output.decode('utf-8'))

    @contextmanager
    def deploy_agent(self, configmap_path, daemonset_path, serviceaccount_path, observer=None, monitors=[], cluster_name="minikube", backend=None, image_name=None, image_tag=None, namespace="default"):
        self.pull_agent_image(image_name, tag=image_tag)
        try:
            self.agent.deploy(self.client, configmap_path, daemonset_path, serviceaccount_path, observer, monitors, cluster_name=cluster_name, backend=backend, image_name=image_name, image_tag=image_tag, namespace=namespace)
        except Exception as e:
            print("\n\n%s\n\n" % get_all_logs(self))
            raise
        try:
            yield self.agent
        finally:
            self.agent.delete()
            self.agent = Agent()

    def get_container_logs(self):
        try:
            return self.container.logs().decode('utf-8').strip()
        except Exception as e:
            return "Failed to get minikube container logs!\n%s" % str(e)
