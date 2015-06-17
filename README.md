# Introduction

Evacuationd is a deameon that is designed for maintaining evacuation process of instances in case of compute failure. It is intended to work with pacemaker, but any other cluster manager that is able to run simple script in case of compute failure would work.

# How it works

Evacuationd is an active-active daemon that is able to send messages onto RabbitMQ queues and to receive them. For every received message, there is an action that daemon will perform. An acknowlage is send back to RabbitMQ only if action ends successfuly. Doing so, if particular daemon dies while doing an action, message will be resend and some other instance of evacuationd will do the job. The possible actions are:
1. Host-evacuate - Ask nova for instances running on given host, and for every instance send message 'Vm-evacuate'
2. Vm-evacuate - Evacuate given VM.

If an exception occures while proccessing an action, message related with it is resend, so this action will be retry later.

![evacuationdworkflow](https://raw.githubusercontent.com/dawiddeja/evacuationd/master/workflow.jpg)

# Future work

1. Enable usage of acknowlages in OpenStack Oslo, so it can be used instead of pika;
2. Add 3rd Action - Look for VM - it will check if given VM ended up in active state on new hosts; if no, VM can be rebuild
