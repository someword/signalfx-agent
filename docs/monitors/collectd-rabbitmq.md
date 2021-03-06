<!--- GENERATED BY gomplate from scripts/docs/monitor-page.md.tmpl --->

# collectd/rabbitmq

 Monitors an instance of RabbitMQ using the
[collectd RabbitMQ Python
Plugin](https://github.com/signalfx/collectd-rabbitmq).

See the [integration
doc](https://github.com/signalfx/integrations/tree/master/collectd-rabbitmq)
for more information.


Monitor Type: `collectd/rabbitmq`

[Monitor Source Code](https://github.com/signalfx/signalfx-agent/tree/master/internal/monitors/collectd/rabbitmq)

**Accepts Endpoints**: **Yes**

**Multiple Instances Allowed**: Yes

## Configuration

| Config option | Required | Type | Description |
| --- | --- | --- | --- |
| `host` | **yes** | `string` |  |
| `port` | **yes** | `integer` |  |
| `brokerName` | no | `string` | The name of the particular RabbitMQ instance.  Can be a Go template using other config options. This will be used as the `plugin_instance` dimension. (**default:** `{{.host}}-{{.port}}`) |
| `collectChannels` | no | `bool` |  (**default:** `false`) |
| `collectConnections` | no | `bool` |  (**default:** `false`) |
| `collectExchanges` | no | `bool` |  (**default:** `false`) |
| `collectNodes` | no | `bool` |  (**default:** `false`) |
| `collectQueues` | no | `bool` |  (**default:** `false`) |
| `httpTimeout` | no | `integer` |  (**default:** `0`) |
| `verbosityLevel` | no | `string` |  |
| `username` | **yes** | `string` |  |
| `password` | **yes** | `string` |  |




## Metrics

This monitor emits the following metrics.  Note that configuration options may
cause only a subset of metrics to be emitted.

| Name | Type | Description |
| ---  | ---  | ---         |
| `counter.channel.message_stats.ack` | counter | The number of acknowledged messages |
| `counter.channel.message_stats.confirm` | counter | Count of messages confirmed. |
| `counter.channel.message_stats.deliver` | counter | Count of messages delivered in acknowledgement mode to consumers. |
| `counter.channel.message_stats.deliver_get` | counter | Count of all messages delivered on the channel |
| `counter.channel.message_stats.publish` | counter | Count of messages published. |
| `counter.connection.channel_max` | counter | The maximum number of channels on the connection |
| `counter.connection.recv_cnt` | counter | Number of packets received on the connection |
| `counter.connection.recv_oct` | counter | Number of octets received on the connection |
| `counter.connection.send_cnt` | counter | Number of packets sent by the connection |
| `counter.connection.send_oct` | counter | Number of octets sent by the connection |
| `counter.exchange.message_stats.confirm` | counter | Count of messages confirmed. |
| `counter.exchange.message_stats.publish_in` | counter | Count of messages published "in" to an exchange, i.e. not taking account of routing. |
| `counter.exchange.message_stats.publish_out` | counter | Count of messages published "out" of an exchange, i.e. taking account of routing. |
| `counter.node.io_read_bytes` | counter | Total number of bytes read from disk by the persister. |
| `counter.node.io_read_count` | counter | Total number of read operations by the persister. |
| `counter.node.mnesia_disk_tx_count` | counter | Number of Mnesia transactions which have been performed that required writes to disk. |
| `counter.node.mnesia_ram_tx_count` | counter | Number of Mnesia transactions which have been performed that did not require writes to disk. |
| `counter.queue.disk_reads` | counter | Total number of times messages have been read from disk by this queue since it started. |
| `counter.queue.disk_writes` | counter | Total number of times messages have been written to disk by this queue since it started. |
| `counter.queue.message_stats.ack` | counter | Number of acknowledged messages processed by the queue |
| `counter.queue.message_stats.deliver` | counter | Count of messages delivered in acknowledgement mode to consumers. |
| `counter.queue.message_stats.deliver_get` | counter | Count of all messages delivered on the queue |
| `counter.queue.message_stats.publish` | counter | Count of messages published. |
| `gauge.channel.connection_details.peer_port` | gauge | The peer port number of the channel |
| `gauge.channel.consumer_count` | gauge | The number of consumers the channel has |
| `gauge.channel.global_prefetch_count` | gauge | QoS prefetch limit for the entire channel, 0 if unlimited. |
| `gauge.channel.message_stats.ack_details.rate` | gauge | How much the channel message ack count has changed per second in the most recent sampling interval. |
| `gauge.channel.message_stats.confirm_details.rate` | gauge | How much the channel message confirm count has changed per second in the most recent sampling interval. |
| `gauge.channel.message_stats.deliver_details.rate` | gauge | How much the channel deliver count has changed per second in the most recent sampling interval. |
| `gauge.channel.message_stats.deliver_get_details.rate` | gauge | How much the channel message count has changed per second in the most recent sampling interval. |
| `gauge.channel.message_stats.publish_details.rate` | gauge | How much the channel message publish count has changed per second in the most recent sampling interval. |
| `gauge.channel.messages_unacknowledged` | gauge | Number of messages delivered via this channel but not yet acknowledged. |
| `gauge.channel.messages_uncommitted` | gauge | Number of messages received in an as yet uncommitted transaction. |
| `gauge.channel.messages_unconfirmed` | gauge | Number of published messages not yet confirmed. On channels not in confirm mode, this remains 0. |
| `gauge.channel.number` | gauge | The number of the channel, which uniquely identifies it within a connection. |
| `gauge.channel.prefetch_count` | gauge | QoS prefetch limit for new consumers, 0 if unlimited. |
| `gauge.connection.channels` | gauge | The current number of channels on the connection |
| `gauge.connection.connected_at` | gauge | The integer timestamp of the most recent time the connection was established |
| `gauge.connection.frame_max` | gauge | Maximum permissible size of a frame (in bytes) to negotiate with clients. |
| `gauge.connection.peer_port` | gauge | The peer port of the connection |
| `gauge.connection.port` | gauge | The port the connection is established on |
| `gauge.connection.recv_oct_details.rate` | gauge | How much the connection's octets received count has changed per second in the most recent sampling interval. |
| `gauge.connection.send_oct_details.rate` | gauge | How much the connection's octets sent count has changed per second in the most recent sampling interval. |
| `gauge.connection.send_pend` | gauge | The number of messages in the send queue of the connection |
| `gauge.connection.timeout` | gauge | The current timeout setting (in seconds) of the connection |
| `gauge.exchange.message_stats.confirm_details.rate` | gauge | How much the message confirm count has changed per second in the most recent sampling interval. |
| `gauge.exchange.message_stats.publish_in_details.rate` | gauge | How much the exchange publish-in count has changed per second in the most recent sampling interval. |
| `gauge.exchange.message_stats.publish_out_details.rate` | gauge | How much the exchange publish-out count has changed per second in the most recent sampling interval. |
| `gauge.node.disk_free` | gauge | Disk free space (in bytes) on the node |
| `gauge.node.disk_free_details.rate` | gauge | How much the disk free space has changed per second in the most recent sampling interval. |
| `gauge.node.disk_free_limit` | gauge | Point (in bytes) at which the disk alarm will go off. |
| `gauge.node.fd_total` | gauge | Total number of file descriptors available. |
| `gauge.node.fd_used` | gauge | Number of used file descriptors. |
| `gauge.node.fd_used_details.rate` | gauge | How much the number of used file descriptors has changed per second in the most recent sampling interval. |
| `gauge.node.io_read_avg_time` | gauge | Average wall time (milliseconds) for each disk read operation in the last statistics interval. |
| `gauge.node.io_read_avg_time_details.rate` | gauge | How much the I/O read average time has changed per second in the most recent sampling interval. |
| `gauge.node.io_read_bytes_details.rate` | gauge | How much the number of bytes read from disk has changed per second in the most recent sampling interval. |
| `gauge.node.io_read_count_details.rate` | gauge | How much the number of read operations has changed per second in the most recent sampling interval. |
| `gauge.node.io_sync_avg_time` | gauge | Average wall time (milliseconds) for each fsync() operation in the last statistics interval. |
| `gauge.node.io_sync_avg_time_details.rate` | gauge | How much the average I/O sync time has changed per second in the most recent sampling interval. |
| `gauge.node.io_write_avg_time` | gauge | Average wall time (milliseconds) for each disk write operation in the last statistics interval. |
| `gauge.node.io_write_avg_time_details.rate` | gauge | How much the I/O write time has changed per second in the most recent sampling interval. |
| `gauge.node.mem_limit` | gauge | Point (in bytes) at which the memory alarm will go off. |
| `gauge.node.mem_used` | gauge | Memory used in bytes. |
| `gauge.node.mem_used_details.rate` | gauge | How much the count has changed per second in the most recent sampling interval. |
| `gauge.node.mnesia_disk_tx_count_details.rate` | gauge | How much the Mnesia disk transaction count has changed per second in the most recent sampling interval. |
| `gauge.node.mnesia_ram_tx_count_details.rate` | gauge | How much the RAM-only Mnesia transaction count has changed per second in the most recent sampling interval. |
| `gauge.node.net_ticktime` | gauge | Current kernel net_ticktime setting for the node. |
| `gauge.node.proc_total` | gauge | The maximum number of Erlang processes that can run in an Erlang VM. |
| `gauge.node.proc_used` | gauge | Number of Erlang processes currently running in use. |
| `gauge.node.proc_used_details.rate` | gauge | How much the number of erlang processes in use has changed per second in the most recent sampling interval. |
| `gauge.node.processors` | gauge | Number of cores detected and usable by Erlang. |
| `gauge.node.run_queue` | gauge | Average number of Erlang processes waiting to run. |
| `gauge.node.sockets_total` | gauge | Number of file descriptors available for use as sockets. |
| `gauge.node.sockets_used` | gauge | Number of file descriptors used as sockets. |
| `gauge.node.sockets_used_details.rate` | gauge | How much the number of sockets used has changed per second in the most recent sampling interval. |
| `gauge.node.uptime` | gauge | Time since the Erlang VM started, in milliseconds. |
| `gauge.queue.backing_queue_status.avg_ack_egress_rate` | gauge | Rate at which unacknowledged message records leave RAM, e.g. because acks arrive or unacked messages are paged out |
| `gauge.queue.backing_queue_status.avg_ack_ingress_rate` | gauge | Rate at which unacknowledged message records enter RAM, e.g. because messages are delivered requiring acknowledgement |
| `gauge.queue.backing_queue_status.avg_egress_rate` | gauge | Average egress (outbound) rate, not including messages that are sent straight through to auto-acking consumers. |
| `gauge.queue.backing_queue_status.avg_ingress_rate` | gauge | Average ingress (inbound) rate, not including messages that are sent straight through to auto-acking consumers. |
| `gauge.queue.backing_queue_status.len` | gauge | Total backing queue length, in messages |
| `gauge.queue.backing_queue_status.next_seq_id` | gauge | The next sequence ID to be used in the backing queue |
| `gauge.queue.backing_queue_status.q1` | gauge | Number of messages in backing queue q1 |
| `gauge.queue.backing_queue_status.q2` | gauge | Number of messages in backing queue q2 |
| `gauge.queue.backing_queue_status.q3` | gauge | Number of messages in backing queue q3 |
| `gauge.queue.backing_queue_status.q4` | gauge | Number of messages in backing queue q4 |
| `gauge.queue.consumer_utilisation` | gauge | Fraction of the time (between 0.0 and 1.0) that the queue is able to immediately deliver messages to consumers. |
| `gauge.queue.consumers` | gauge | Number of consumers of the queue |
| `gauge.queue.memory` | gauge | Bytes of memory consumed by the Erlang process associated with the queue, including stack, heap and internal structures. |
| `gauge.queue.message_bytes` | gauge | Sum of the size of all message bodies in the queue. This does not include the message properties (including headers) or any overhead. |
| `gauge.queue.message_bytes_persistent` | gauge | Total number of persistent messages in the queue (will always be 0 for transient queues). |
| `gauge.queue.message_bytes_ram` | gauge | Like message_bytes but counting only those messages which are in RAM. |
| `gauge.queue.message_bytes_ready` | gauge | Like message_bytes but counting only those messages ready to be delivered to clients. |
| `gauge.queue.message_bytes_unacknowledged` | gauge | Like message_bytes but counting only those messages delivered to clients but not yet acknowledged. |
| `gauge.queue.message_stats.ack_details.rate` | gauge | How much the number of acknowledged messages has changed per second in the most recent sampling interval. |
| `gauge.queue.message_stats.deliver_details.rate` | gauge | How much the count of messages delivered has changed per second in the most recent sampling interval. |
| `gauge.queue.message_stats.deliver_get_details.rate` | gauge | How much the count of all messages delivered has changed per second in the most recent sampling interval. |
| `gauge.queue.message_stats.publish_details.rate` | gauge | How much the count of messages published has changed per second in the most recent sampling interval. |
| `gauge.queue.messages` | gauge | Sum of ready and unacknowledged messages (queue depth). |
| `gauge.queue.messages_details.rate` | gauge | How much the queue depth has changed per second in the most recent sampling interval. |
| `gauge.queue.messages_persistent` | gauge | Total number of persistent messages in the queue (will always be 0 for transient queues). |
| `gauge.queue.messages_ram` | gauge | Total number of messages which are resident in RAM. |
| `gauge.queue.messages_ready` | gauge | Number of messages ready to be delivered to clients. |
| `gauge.queue.messages_ready_details.rate` | gauge | How much the count of messages ready has changed per second in the most recent sampling interval. |
| `gauge.queue.messages_ready_ram` | gauge | Number of messages from messages_ready which are resident in RAM. |
| `gauge.queue.messages_unacknowledged` | gauge | Number of messages delivered to clients but not yet acknowledged. |
| `gauge.queue.messages_unacknowledged_details.rate` | gauge | How much the count of unacknowledged messages has changed per second in the most recent sampling interval. |
| `gauge.queue.messages_unacknowledged_ram` | gauge | Number of messages from messages_unacknowledged which are resident in RAM. |



