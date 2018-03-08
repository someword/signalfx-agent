# Frequently Asked Questions

- [How does this differ from the old collectd agent?](#how-does-this-differ-from-the-old-collectd-agent)
- [What if I am currently using the old collectd agent?](#what-if-I-am-currently-using-the-old-collectd-agent)
- [How can I see the datapoints emitted by the agent to troubleshoot issues?](#how-can-I-see-the-datapoints-emitted-by-the-agent-to-troubleshoot-issues)
- [How can I see what services the agent has discovered?](#how-can-I-see-what-services-the-agent-has-discovered)


## How does this differ from the old collectd agent?

The new agent ("SmartAgent") is, at least upon the initial release, basically
a wrapper application around collectd that adds service discovery and automatic
configuration of collectd based on those discovered services.  Most of the
system metrics are generated by collectd, as well as most application metrics.
Configuration of collectd monitors is largely a passthrough to collectd
config options, but in a YAML format instead of the collectd custom syntax.

The first main foray outside of collectd was the Kubernetes integration, which
uses monitors and observers written purely in Go and run completely independent
of collectd.  We hope to write more and more monitors apart from collectd, and
perhaps eventually remove the dependency on collectd entirely.

## What if I am currently using the old collectd agent?

If you are using the old collectd agent, you should uninstall it first before
installing the new agent (the "SmartAgent").  The new agent comes will all of
its dependencies bundled, so you will not need a prior collectd installation.
Make sure the old collectd instance does not run alongside the new agent, or
you might send duplicate datapoints and use unnecessary DPM.

If you have your own homegrown collectd plugins, you can still use these with
the new agent by using the [collectd/custom](./monitors/collectd-custom.md)
monitor.  You can reuse your original collectd `managed_config` directory's
configuration files by adding the following monitor:

```yaml
monitors:
  - type: collectd/custom
    templates: {"#from": "/etc/collectd/managed_config/*.conf", raw: true}
```

We run collectd-python linked against Python 2.7 so any Python plugins will
have to be Python 2.7 compatible.

## How can I see the datapoints emitted by the agent to troubleshoot issues?

Set the following config in the agent.yaml config file:

```yaml
logging:
  level: debug
writer:
  logDatapoints: true
```

This will log all of the datapoints as they are emitted by the agent.

## How can I see what services the agent has discovered?

Run the following command on the host with the agent:

```sh
$ sudo signalfx-agent status
```

If using the containerized agent, you don't need to use `sudo`.

This will dump out some text that includes a section listing the discovered
service endpoints that the agent knows about.