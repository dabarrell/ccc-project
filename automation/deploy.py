import json
import os
from pprint import pprint
from collections import namedtuple
from tempfile import NamedTemporaryFile
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    def v2_runner_on_ok(self, result, **kwargs):
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later
        """
        host = result._host
        print(json.dumps({host.name: result._result}, indent=4))

def deploy(hosts):
    Options = namedtuple('Options', ['connection', 'private_key_file','module_path', 'forks', 'become', 'become_method', 'become_user', 'check'])
    variable_manager = VariableManager()
    loader = DataLoader()

    options = Options(connection='ssh', private_key_file='/Users/david/.ssh/ccc-project', module_path='', forks=100, become=None, become_method='sudo', become_user='root', check=False)
    passwords = dict(vault_pass='')

    results_callback = ResultCallback()

    host_file = NamedTemporaryFile(delete=False)
    host_file.write(b'[servers]\n')
    for h in hosts:
        host_file.write(bytes('{0}\n'.format(h), encoding='utf-8'))
    host_file.close()

    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=host_file.name)
    variable_manager.set_inventory(inventory)

    # create play with tasks
    play_source =  dict(
            name = 'CCC Deploy',
            hosts = 'servers',
            remote_user = 'ubuntu',
            gather_facts = 'no',
            tasks = [
                dict(name="Run a command",
                             action=dict(module="command", args="touch /home/ubuntu/asdfdasdf"),
                             register="output"),
                dict(action=dict(module='shell', args='ls'), register='shell_out'),
                dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
             ]
        )
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # actually run it
    tqm = None
    try:
        tqm = TaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  options=options,
                  passwords=passwords,
                  stdout_callback=results_callback
              )
        result = tqm.run(play)
        pprint(result)
    finally:
        if tqm is not None:
            tqm.cleanup()
        os.remove(host_file.name)