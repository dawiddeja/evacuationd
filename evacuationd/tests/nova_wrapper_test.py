import unittest
import uuid
from mock import patch, MagicMock

from evacuationd.nova_wrapper import NovaWrapper
from evacuationd.commons import common


class TestNovaWrapper(unittest.TestCase):

    def setUp(self):
        self._original_read_config = common.read_config
        common.read_config = lambda x: {
            'admin_user': 'admin',
            'admin_password': 'password',
            'admin_tenant_name': 'tenant',
            'auth_uri': 'http://localhost:35357/v2.0/'
        }
        self.nova = NovaWrapper(True)

    @patch('evacuationd.nova_wrapper.NovaWrapper._is_host_evacuable')
    @patch('evacuationd.nova_wrapper.NovaWrapper._get_evacuable_flavors')
    @patch('novaclient.v1_1.servers.ServerManager.list')
    @patch('novaclient.v1_1.hypervisors.HypervisorManager.search')
    def test_list_vms_no_vms_on_host(self, search, server_list,
                      _get_evacuable_flavors, _is_host_evacuable):
        search.return_value = MagicMock()
        server_list.return_value = []
        _get_evacuable_flavors.return_value = []
        _is_host_evacuable.return_value = True

        l = self.nova.list_vms('host')
        self.assertEqual(l, [])

    @patch('evacuationd.nova_wrapper.NovaWrapper._is_host_evacuable')
    @patch('evacuationd.nova_wrapper.NovaWrapper._get_evacuable_flavors')
    @patch('novaclient.v1_1.servers.ServerManager.list')
    @patch('novaclient.v1_1.hypervisors.HypervisorManager.search')
    def test_list_vms_vms_on_host(self, search, server_list,
                      _get_evacuable_flavors, _is_host_evacuable):
        search.return_value = MagicMock()
        server = MagicMock()
        server_id = uuid.uuid4()
        server.id = server_id
        server_list.return_value = [server]
        _get_evacuable_flavors.return_value = []
        _is_host_evacuable.return_value = True

        l = self.nova.list_vms('host')
        self.assertEqual(l[0], server_id)

        _is_host_evacuable.return_value = False
        l = self.nova.list_vms('host')
        self.assertEqual(l, [])
