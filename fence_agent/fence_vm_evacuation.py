#!/usr/bin/python -tt

import sys
import json
import logging
import atexit

import pika

sys.path.append("/usr/share/fence")
from fencing import run_delay, all_opt, atexit_handler, check_input, \
        process_input, show_docs
from evacuationd.commons import action


def define_new_opts():
    all_opt["domain"] = {
        "getopt": "d:",
        "longopt": "domain",
        "help": "-d, --domain=[string]          DNS domain in which hosts"
                         " live, useful when the cluster uses short names and"
                         " nova uses FQDN",
        "required": "0",
        "shortdesc": "DNS domain in which hosts live",
        "default": "",
        "order": 5,
    }
    all_opt["rabbit_hosts"] = {
        "getopt": "r:",
        "longopt": "rabbit_hosts",
        "help": "-r, --rabbit_hosts=host1,host2 List of Rabbitmq servers",
        "required": "1",
        "shortdesc": "List of Rabbitmq servers",
        "default": "",
        "order": 5,
    }
    all_opt["rabbit_port"] = {
        "getopt": "l:",
        "longopt": "rabbit_port",
        "help": "-l, --rabbit_port=int Port to connect to rabbitmq",
        "required": "1",
        "shortdesc": "Port to connect to rabbitmq",
        "default": "",
        "order": 5,
    }
    all_opt["user"] = {
        "getopt": "u:",
        "longopt": "user",
        "help": "-u, --rabbit_user=string User to connect to rabbitmq",
        "required": "1",
        "shortdesc": "User to connect to rabbitmq",
        "default": "",
        "order": 5,
    }
    all_opt["password"] = {
        "getopt": "p:",
        "longopt": "password",
        "help": "-p, --password=string Password to connect to rabbitmq",
        "required": "1",
        "shortdesc": "Password to connect to rabbitmq",
        "default": "",
        "order": 5,
    }


def create_body(host):
    msg = {
        'action': action.ACTION_EVAC_HOST,
        'host': host
    }
    return json.dumps(msg)


def send(user, password, host, port, exchange, routing_key, host_down):
    credentials = pika.PlainCredentials(user, password)
    connection = pika.BlockingConnection(pika. \
            ConnectionParameters(host=host, port=port,
                                 credentials=credentials))

    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, type='direct',
                             auto_delete=True)
    channel.basic_publish(exchange=exchange, routing_key=routing_key,
                          body=create_body(host_down))


def main():
    atexit.register(atexit_handler)

    device_opt = ["rabbit_hosts", "rabbit_port", "user", "domain", "password",
                  "port"]
    define_new_opts()
    all_opt["shell_timeout"]["default"] = "180"

    options = check_input(device_opt, process_input(device_opt))

    docs = {}
    docs["shortdesc"] = "Fence agent for nova compute nodes"
    docs["longdesc"] = "fence_nova_host is a Nova fencing notification agent"
    docs["vendorurl"] = ""

    show_docs(options, docs)

    run_delay(options)

    host = None
    # Potentially we should make this a pacemaker feature
    if options["--domain"] != "" and "--plug" in options:
        options["--plug"] = options["--plug"] + "." + options["--domain"]

    if "--plug" in options:
        host = options["--plug"]

    rabbit_hosts = options["--rabbit_hosts"].split(",")
    port = int(options["--rabbit_port"])
    user = options["--user"]
    password = options["--password"]
    routing_key = 'auto-evac'
    exchange = 'auto-evac'

    if options['--action'] in ['reboot', 'off']:
        if host is None:
            logging.error('No host specified')
            sys.exit(1)

        for rabbit_host in rabbit_hosts:
            try:
                send(user, password, rabbit_host, port, exchange, routing_key,
                     host)
                sys.exit(0)
            except Exception:
                logging.warning('Cannot connect to rabbitmq on %s',
                                rabbit_host)

        logging.error('Cannot connect to any of rabbitmq brokers')
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
