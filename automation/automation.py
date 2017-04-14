import boto
import time
from boto.ec2.regioninfo import RegionInfo


def main():
    global ec2
    ec2 = create_connection()
    print('Connection to NeCTAR established\n')
    instances = create_instances(1)

    for i in instances:
        print(i.id + ':' + i.state)

    print('\nAttaching volumes')
    cont = False
    while not cont:
        cont = True
        for i in instances:
            i.update()
            if i.state == 'running':
                volumes = [v for v in ec2.get_all_volumes() if v.attach_data.instance_id == i.id]
                if len(volumes) == 0:
                    attach_volume(create_vol(10), i.id)
                else:
                    print('Already has volume attached')
            else:
                cont = False
        if cont is False:
            print('Instance(s) still pending - waiting 15 seconds')
            time.sleep(15)

    print('\nIP addresses')
    for i in instances:
        i.update()
        print(i.id + ':' + i.private_ip_address)


def create_connection():
    aws_access_key_id = '***REMOVED***'
    aws_secret_access_key = '***REMOVED***'
    region = RegionInfo(name='melbourne', endpoint='nova.rc.nectar.org.au')
    ec2 = boto.connect_ec2(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                           is_secure=True, region=region, port=8773, path='/services/Cloud', validate_certs=False)
    return ec2


def create_instances(num):
    res = ec2.run_instances(image_id='ami-86f4a44c', key_name='ccc-project', instance_type='m1.small',
                             placement='melbourne-qh2', min_count=num, max_count=num,
                             security_groups=['SSH', 'default'])
    print('Created {0} instances'.format(num))
    return res.instances


def create_vol(size):
    vol = ec2.create_volume(size, 'melbourne-qh2')
    print('Created {0}gb volume: {1}'.format(size, vol.id))
    return vol.id


def attach_volume(vol_id, i_id):
    vol = ec2.get_all_volumes([vol_id])[0]
    if vol.status == 'available':
        ec2.attach_volume(vol.id, i_id, '/dev/vdc')
        print('Attached volume {0} to instance {1}'.format(vol_id,i_id))
    else:
        print('Not available')


def get_instances():
    return ec2.get_only_instances()


def print_instances():
    instances = get_instances()
    for i in instances:
        print(i.id + ':' + i.state)


if __name__ == '__main__':main()