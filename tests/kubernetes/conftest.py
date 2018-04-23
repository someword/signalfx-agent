from tests.helpers.util import *
from tests.kubernetes.minikube import *
from tests.kubernetes.utils import *

import docker
import pytest

AGENT_YAMLS_DIR = os.environ.get("AGENT_YAMLS_DIR", "/go/src/github.com/signalfx/signalfx-agent/deployments/k8s")
AGENT_CONFIGMAP_PATH = os.environ.get("AGENT_CONFIGMAP_PATH", os.path.join(AGENT_YAMLS_DIR, "configmap.yaml"))
AGENT_DAEMONSET_PATH = os.environ.get("AGENT_DAEMONSET_PATH", os.path.join(AGENT_YAMLS_DIR, "daemonset.yaml"))
AGENT_SERVICEACCOUNT_PATH = os.environ.get("AGENT_SERVICEACCOUNT_PATH", os.path.join(AGENT_YAMLS_DIR, "serviceaccount.yaml"))
AGENT_IMAGE_NAME = os.environ.get("AGENT_IMAGE_NAME", "localhost:5000/signalfx-agent")
AGENT_IMAGE_TAG = os.environ.get("AGENT_IMAGE_TAG", "k8s-test")
SERVICES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'services')

@pytest.fixture(scope="module")
def k8s_services():
    services = []
    for service in os.listdir(SERVICES_DIR):
        if service != '__init__.py' and service.endswith('.py'):
            exec("from tests.kubernetes.services import %s" % service[:-3])
            services.append({"name": service[:-3], "config": eval(service[:-3] + ".CONFIG")})
    return services

@pytest.fixture(scope="module")
def backend():
    with fake_backend.start(ip=get_host_ip()) as backend:
        print("\nStarting fake backend ...")
        yield backend

@pytest.fixture(scope="module")
def local_registry(request):
    client = docker.from_env(version='auto')
    final_agent_image_name = request.config.getoption("--k8s-agent-name")
    final_agent_image_tag = request.config.getoption("--k8s-agent-tag")
    try:
        final_image = client.images.get(final_agent_image_name + ":" + final_agent_image_tag)
    except:
        try:
            print("\nAgent image '%s:%s' not found in local registry." % (final_agent_image_name, final_agent_image_tag))
            print("\nAttempting to pull from remote registry ...")
            final_image = client.images.pull(final_agent_image_name, tag=final_agent_image_tag)
        except:
            final_image = None
    assert final_image, "agent image '%s:%s' not found!" % (final_agent_image_name, final_agent_image_tag)
    try:
        client.containers.get("registry")
        print("\nRegistry container localhost:5000 already running")
    except:
        try:
            client.containers.run(
                image='registry:latest',
                name='registry',
                detach=True,
                ports={'5000/tcp': 5000})
            print("\nStarted registry container localhost:5000")
        except:
            pass
        print("\nWaiting for registry container localhost:5000 to be ready ...")
        start_time = time.time()
        while True:
            assert (time.time() - start_time) < 30, "timed out waiting for registry container to be ready!"
            try:
                client.containers.get("registry")
                time.sleep(2)
                break
            except:
                time.sleep(2)
    print("\nTagging %s:%s as %s:%s ..." % (final_agent_image_name, final_agent_image_tag, AGENT_IMAGE_NAME, AGENT_IMAGE_TAG))
    final_image.tag(AGENT_IMAGE_NAME, tag=AGENT_IMAGE_TAG)
    print("\nPushing %s:%s ..." % (AGENT_IMAGE_NAME, AGENT_IMAGE_TAG))
    client.images.push(AGENT_IMAGE_NAME, tag=AGENT_IMAGE_TAG)
    yield
    try:
        client.containers.get("registry").remove(force=True)
    except:
        pass

@pytest.fixture(scope="module")
def minikube(request, backend, local_registry, k8s_services):
    k8s_version, k8s_observer = request.param
    k8s_timeout = int(request.config.getoption("--k8s-timeout"))
    k8s_container = request.config.getoption("--k8s-container")
    monitors = [m[0] for m in getattr(request.module, "MONITORS_TO_TEST")]
    mk = Minikube()
    if k8s_container:
        mk.connect(k8s_container, k8s_timeout)
        for service in k8s_services:
            assert len(get_all_pods_matching_name(service["config"]["pod_name"])) == 0, "service \"%s\" already running in container %s!" % (service["name"], mk.container.name)
        assert len(get_all_pods_matching_name('signalfx-agent.*')) == 0, "signalfx-agent already running in container %s!" % mk.container.name
    else:
        name = "minikube-%s-%s" % (k8s_version, k8s_observer)
        mk.deploy(k8s_version, k8s_timeout, name=name)
    mk.deploy_services(k8s_services)
    mk.deploy_agent(
        AGENT_CONFIGMAP_PATH,
        AGENT_DAEMONSET_PATH,
        AGENT_SERVICEACCOUNT_PATH,
        k8s_observer,
        monitors,
        cluster_name="minikube",
        backend=backend,
        image_name=AGENT_IMAGE_NAME,
        image_tag=AGENT_IMAGE_TAG,
        namespace="default")
    def teardown():
        if not k8s_container:
            try:
                mk.container.remove(force=True, v=True)
            except:
                pass
    request.addfinalizer(teardown)
    return mk

@pytest.fixture
def k8s_test_timeout(request):
    return int(request.config.getoption("--k8s-test-timeout"))
