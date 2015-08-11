import json
import ConfigParser
from evacuationd.commons import action


def create_vm_message(vm_id, host):
    msg = {
        'action': action.ACTION_EVAC_VM,
        'vm': vm_id,
        'host': host
    }
    return json.dumps(msg)


def read_config(section):
    conf_dict = {}
    config = ConfigParser.ConfigParser()
    config.read('/etc/evacuationd/evacuationd.conf')

    options = config.options(section)
    for option in options:
        try:
            conf_dict[option] = get_option(config, section, option)
        except:
            conf_dict[option] = None

    return conf_dict


def get_option(config, section, option):
    type_map = {'on_shared_storage': config.getboolean,
                'port': config.getint}

    parse_func = type_map.get(option, config.get)
    opt = parse_func(section, option)

    if option in ['hosts']:
        opt = opt.split(',')

    return opt
