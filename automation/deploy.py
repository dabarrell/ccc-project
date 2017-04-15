import boto
import time
import paramiko
import os
import sys
from deploy import deploy
from boto.ec2.regioninfo import RegionInfo

aws_access_key_id = '3161434dc53f435b81132e9743f8bdad'
aws_secret_access_key = 'bf6dd7caf81f44719a5a28a7201bf007'

num_of_instances = 4
instance_type = 'm1.medium'
volume_size = 50


def main():
    global ec2
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
                    vol_id = create_vol(volume_size)
                    attach_volume(vol_id, i.id)
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
    status, message = deploy(hosts)
    print(message)
    print("--- %s seconds ---" % (time.time() - start_time))
    sys.exit(status)


def create_connection():
    region = RegionInfo(name='melbourne', endpoint='nova.rc.nectar.org.au')
    ec2 = boto.connect_ec2(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                           is_secure=True, region=region, port=8773, path='/services/Cloud', validate_certs=False)
    return ec2


def create_instances(num):
    res = ec2.run_instances(image_id='ami-86f4a44c', key_name='ccc-project', instance_type=instance_type,
                             placement='melbourne-qh2', min_count=num, max_count=num,
                             security_groups=['CCC', 'SSH', 'default'])
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
            client.connect(h, username='ubuntu', key_filename='/Users/david/.ssh/ccc-project')
            client.close()
            print('Connection to ' + h + ' successful')
        except paramiko.ssh_exception.NoValidConnectionsError:
            print('Unable to connect to ' + h)
            res = False
    return res


if __name__ == '__main__':main()