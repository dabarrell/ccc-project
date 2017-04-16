import os
import json
from tempfile import NamedTemporaryFile
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback.default import CallbackModule

private_key_file = os.getenv('CCC_PRIVATE_KEY') or os.path.expanduser('~/.ssh/ccc-project')


class Options(object):
    """
    Options class to replace Ansible OptParser
    """
    def __init__(self, verbosity=None, inventory=None, listhosts=None, subset=None, module_paths=None, extra_vars=None,
                 forks=None, ask_vault_pass=None, vault_password_files=None, new_vault_password_file=None,
                 output_file=None, tags=[], skip_tags=[], one_line=None, tree=None, ask_sudo_pass=None, ask_su_pass=None,
                 sudo=None, sudo_user=None, become=None, become_method=None, become_user=None, become_ask_pass=None,
                 ask_pass=None, private_key_file=None, remote_user=None, connection=None, timeout=None, ssh_common_args=None,
                 sftp_extra_args=None, scp_extra_args=None, ssh_extra_args=None, poll_interval=None, seconds=None, check=None,
                 syntax=None, diff=None, force_handlers=None, flush_cache=None, listtasks=None, listtags=None, module_path=None):
        self.verbosity = verbosity
        self.inventory = inventory
        self.listhosts = listhosts
        self.subset = subset
        self.module_paths = module_paths
        self.extra_vars = extra_vars
        self.forks = forks
        self.ask_vault_pass = ask_vault_pass
        self.vault_password_files = vault_password_files
        self.new_vault_password_file = new_vault_password_file
        self.output_file = output_file
        self.tags = tags
        self.skip_tags = skip_tags
        self.one_line = one_line
        self.tree = tree
        self.ask_sudo_pass = ask_sudo_pass
        self.ask_su_pass = ask_su_pass
        self.sudo = sudo
        self.sudo_user = sudo_user
        self.become = become
        self.become_method = become_method
        self.become_user = become_user
        self.become_ask_pass = become_ask_pass
        self.ask_pass = ask_pass
        self.private_key_file = private_key_file
        self.remote_user = remote_user
        self.connection = connection
        self.timeout = timeout
        self.ssh_common_args = ssh_common_args
        self.sftp_extra_args = sftp_extra_args
        self.scp_extra_args = scp_extra_args
        self.ssh_extra_args = ssh_extra_args
        self.poll_interval = poll_interval
        self.seconds = seconds
        self.check = check
        self.syntax = syntax
        self.diff = diff
        self.force_handlers = force_handlers
        self.flush_cache = flush_cache
        self.listtasks = listtasks
        self.listtags = listtags
        self.module_path = module_path


class ResultCallback(CallbackModule):
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
        # print(json.dumps({host.name: result._result}, indent=4))
        super(ResultCallback, self).v2_runner_on_ok(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host
        print(json.dumps({host.name: result._result}, indent=4))
        super(ResultCallback, self).v2_runner_on_failed(result, ignore_errors)


def runPlaybook(hosts, playbook, tags=[], private_key_file=private_key_file):
    variable_manager = VariableManager()
    loader = DataLoader()

    options = Options(connection='ssh', private_key_file=private_key_file, module_path='', forks=100, become=True, become_method='sudo', become_user='root', check=False, tags=tags)
    passwords = dict(vault_pass='')

    results_callback = ResultCallback()

    host_file = NamedTemporaryFile(delete=False)
    host_file.write(b'[servers]\n')
    for h in hosts:
        host_file.write(bytes('{0}\n'.format(h), encoding='utf-8'))
    host_file.close()

    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=host_file.name)
    variable_manager.set_inventory(inventory)

    pbex = PlaybookExecutor(
        playbooks=[playbook],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=options,
        passwords=passwords
    )
    pbex._tqm._stdout_callback = results_callback
    result = pbex.run()
    stats = pbex._tqm._stats

    outputs = {0: 'Deployment successful',
               1: 'Error occurred during deployment',
               2: 'One or more hosts failed',
               4: 'One or more hosts unreachable',
               255: 'Unknown error occurred during deployment'
               }

    run_success = True
    hosts = sorted(stats.processed.keys())
    for h in hosts:
        t = stats.summarize(h)
        if t['unreachable'] > 0 or t['failures'] > 0:
            run_success = False

    os.remove(host_file.name)

    try:
        out = outputs[result]
    except KeyError:
        out = 'Unrecognised error code'
    return result, out

if __name__ == '__main__':
    runPlaybook(['115.146.88.201', '115.146.88.204'],
                '/Users/david/Workspace/uni/CCC/ccc-project/automation/playbook/playbook.yml')