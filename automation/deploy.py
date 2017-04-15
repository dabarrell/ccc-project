#!/usr/bin/env python
import boto
import time
import paramiko
import os
import sys
from ansible_functions import runPlaybook
from boto.ec2.regioninfo import RegionInfo

num_of_instances = 1
instance_type = 'm1.medium'
volume_size = 50
playbook_file_name = 'playbook/playbook.yml'

aws_access_key_id = '3161434dc53f435b81132e9743f8bdad'
aws_secret_access_key = 'bf6dd7caf81f44719a5a28a7201bf007'

private_key_file = os.getenv('CCC_PRIVATE_KEY') or os.path.expanduser('~/.ssh/ccc-project')


def main():
    global ec2
    if not os.path.isfile(private_key_file):
        print('Error: Private key not found. Please set CCC_PRIVATE_KEY environmental variable, or place at ~/.ssh/ccc-project.')
        sys.exit(1)
    if not oct(os.stat('/Users/david/.ssh/ccc-project').st_mode & 0o0077) == oct(0):
        print('Error: Private key permissions too open. Please restrict to 600.')
        sys.exit(1)

    start_time = time.time()
    ec2 = create_connection()
    print('------ Connection to NeCTAR established ------\n')
    print('Creating {0} instances of type {1}'.format(num_of_instances, instance_type))
    instances = create_instances(num_of_instances)

    for i in instances:
        print(i.id + ':' + i.state)

    print('\n------ Attaching volumes ------')
    cont = False
    while not cont:
        cont = True
        vols = ec2.get_all_volumes()
        for i in instances:
            i.update()
            if i.state == 'running':
                volumes = [v for v in vols if v.attach_data.instance_id == i.id]
                if len(volumes) == 0:
                    try:
                        vol_id = create_vol(volume_size)
                    except:
                        print('Failed to create volume')
                        continue
                    try:
                        attach_volume(vol_id, i.id)
                    except:
                        print(' - failed to attach volume')
                        continue
            else:
                cont = False
                break
        if cont is False:
            print('One or more instances still spawning - waiting 15 seconds')
            time.sleep(15)

    print('\n------ IP addresses ------')
    hosts = []
    for i in instances:
        print(i.id + ':' + i.private_ip_address)
        hosts.append(i.private_ip_address)

    print('\n------ Checking SSH ------')
    while True:
        if check_ssh(hosts) is True:
            break
        print('SSH not yet active on all instances - waiting 15 seconds\n')
        time.sleep(15)

    print('\nDeploying to ' + str(hosts))
    pb_dir = os.path.dirname(os.path.abspath(__file__))
    playbook = "%s/%s" % (pb_dir, playbook_file_name)

    status, message = runPlaybook(hosts, playbook=playbook, private_key_file=private_key_file)
    print(message)
    print("------ %s seconds ------" % (time.time() - start_time))
    sys.exit(status)


def create_connection():
    region = RegionInfo(name='melbourne', endpoint='nova.rc.nectar.org.au')
    ec2 = boto.connect_ec2(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                           is_secure=True, region=region, port=8773, path='/services/Cloud', validate_certs=False)
    return ec2


def create_instances(num):
    res = ec2.run_instances(image_id='ami-86f4a44c', key_name='ccc-project', instance_type=instance_type,
                             placement='melbourne-qh2', min_count=num, max_count=num,
                             security_groups=['CCC', 'SSH', 'default', 'CouchDB'])
    return res.instances


def create_vol(size):
    vol = ec2.create_volume(size, 'melbourne-qh2')
    print('Created {0}gb volume: {1}'.format(size, vol.id), end='')
    return vol.id


def attach_volume(vol_id, i_id):
    vol = ec2.get_all_volumes([vol_id])[0]
    if vol.status == 'available':
        ec2.attach_volume(vol.id, i_id, '/dev/vdc')
        print(' - attached to instance {0}'.format(i_id))
    else:
        print('Not available')


def get_instances():
    return ec2.get_only_instances()


def print_instances():
    instances = get_instances()
    for i in instances:
        print(i.id + ':' + i.state)


class MissingKeyPolicy(paramiko.client.AutoAddPolicy):
    def missing_host_key(self, client, hostname, key):
        with open(os.path.expanduser('~/.ssh/known_hosts'), 'a') as f:
            f.write('%s %s %s\n' % (hostname, 'ssh-rsa', key.get_base64()))
        super(MissingKeyPolicy, self).missing_host_key(client, hostname, key)


def check_ssh(hosts):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(MissingKeyPolicy())
    client.load_system_host_keys()
    res = True
    for h in hosts:
        try:
            client.connect(h, username='ubuntu', key_filename=private_key_file)
            client.close()
            print('Connection to ' + h + ' successful')
        except paramiko.ssh_exception.NoValidConnectionsError:
            print('Unable to connect to ' + h)
            res = False
    return res


if __name__ == '__main__':main()