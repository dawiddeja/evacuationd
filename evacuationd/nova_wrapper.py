import logging

from novaclient import client

from evacuationd.commons import common


class NovaWrapper(object):

    def __init__(self, on_shared_storage):
        self._logger = logging.getLogger(__name__)
        openrc = common.read_config('keystone_authtoken')
        self._nova = client.Client(2,
                                   openrc['admin_user'],
                                   openrc['admin_password'],
                                   openrc['admin_tenant_name'],
                                   openrc['auth_uri'])
        self._on_shared_storage = on_shared_storage

    def list_vms(self, host):
        self._logger.debug('List VMs')

        result = []
        hypervisor = self._nova.hypervisors.search(host, servers=True)[0]

        if hasattr(hypervisor, 'servers'):
            for server in hypervisor.servers:
                result.append(server['uuid'])

        self._logger.debug('Result: %s', str(result))
        return result

    def evac_vm(self, vm_id, host):
        vm = self._nova.servers.get(vm_id)
        if vm.to_dict()['OS-EXT-SRV-ATTR:hypervisor_hostname'] == host:
            vm.evacuate(on_shared_storage=self._on_shared_storage)
        self._logger.info('Request to evacuate VM %s accepted', vm_id)

    def is_host_up(self, host):
        self._logger.debug('Is host up')

        hypervisor = self._nova.hypervisors.search(host)[0]

        return True if hypervisor.state == 'up' else False
