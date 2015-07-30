import logging
import json
import time
import traceback

import pika

from novaclient.exceptions import NotFound, BadRequest

from evacuationd.commons import common, action
from evacuationd.nova_wrapper import NovaWrapper


class AmqpError(Exception):
    pass


class AmqpConnectionError(AmqpError):
    pass


class AmqpChannelError(AmqpError):
    pass


class Amqp(object):

    ROUTING_KEY = 'auto-evac'
    QUEUE_NAME = 'auto-evac'

    def __init__(self):
        self._logger = logging.getLogger(__name__)

        conf = common.read_config('default')

        self._exchange = conf['exchange']
        self._nova = NovaWrapper(conf['on_shared_storage'])
        self._channel = None

        credentials = pika.PlainCredentials(conf['user'], conf['password'])

        connection = None
        for host in conf['hosts']:
            try:
                connection = pika.BlockingConnection(pika. \
                        ConnectionParameters(host=host, port=conf['port'],
                                             credentials=credentials))
                self._logger.info('Connected to %s', str(host))
                break
            except pika.exceptions.AMQPConnectionError as err:
                self._logger.warning('Cannot connect to host %s', host)
                self._logger.debug(str(err))

        if connection is None:
            raise AmqpConnectionError("Cannot connect to any provided hosts")

        try:
            self._channel = connection.channel()
        except pika.exceptions.AMQPChannelError as err:
            self._logger.warning('Cannot connect to host %s', host)
            self._logger.debug(str(err))
            raise AmqpChannelError(err.message)

        self._channel.exchange_declare(exchange=conf['exchange'],
                                       type='direct', auto_delete=True)

    def listen(self):
        if self._nova:
            self._logger.info("Starting listening...")
            self._channel.queue_declare(queue=Amqp.QUEUE_NAME,
                                        auto_delete=False)
            self._channel.queue_bind(queue=Amqp.QUEUE_NAME,
                                     exchange=self._exchange,
                                     routing_key=Amqp.ROUTING_KEY)

            self._channel.basic_consume(self._consume, queue=Amqp.QUEUE_NAME,
                                        no_ack=False)
            self._logger.info('Done')

            self._channel.start_consuming()
        else:
            self._logger.warning("You must provide openrc to enable listening")

    def send(self, body):
        self._channel.basic_publish(exchange=self._exchange,
                                    routing_key=Amqp.ROUTING_KEY, body=body)

    def _consume(self, ch, method, properties, body):
        self._logger.info("Received message")
        self._logger.debug("Body: %s", str(body))

        try:
            msg = json.loads(body)
        except (ValueError, TypeError) as err:
            self._logger.error("Failed to convert message body into dict")
            self._logger.debug(err.message)
            return

        resend_flag = False
        try:
            if msg['action'] == action.ACTION_EVAC_HOST:
                resend_flag = True
                self._evac_host(msg['host'])
            elif msg['action'] == action.ACTION_EVAC_VM:
                resend_flag = True
                self._evac_vm(msg['vm'], msg['host'])
            elif msg['action'] == action.ACTION_DUMMY:
                self._logger.info("Dummy action: %s", str(msg['dummy']))
        except Exception as err:  # orety/
            self._logger.error("There was an error while consuming msg")
            self._logger.debug(type(err))
            self._logger.debug(traceback.format_exc())
            if resend_flag:
                self.send(body)
            # without this, there will be a lot of messages in case of nova
            # temporary failure
            time.sleep(1)
        finally:
            self._channel.basic_ack(delivery_tag=method.delivery_tag)

    def _evac_host(self, host):
        try:
            if self._nova.is_host_up(host):
                self._logger.info('Host %s is still up. Cannot evacuate', host)
            else:
                for server in self._nova.list_vms(host):
                    self._logger.debug('Sending evacuate message for %s',
                                       server)
                    self.send(common.create_vm_message(server, host))
        except NotFound:
            self._logger.error('Host %s not found', host)

    def _evac_vm(self, vm_id, host):
        try:
            self._nova.evac_vm(vm_id, host)
        except BadRequest as err:
            self._logger.error('Cannot evacuate instance - bad request')
            self._logger.debug(str(err))
