import boto3
import boto
from boto.ec2.regioninfo import RegionInfo

aws_access_key_id = '***REMOVED***'
aws_secret_access_key = '***REMOVED***'
region = RegionInfo(name='melbourne', endpoint='nova.rc.nectar.org.au')
print(1)
# ec2 = boto3.resource('ec2',aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
#                      endpoint_url='https://nova.rc.nectar.org.au', region_name='melbourne', verify=False)
# print(1.5)
conn = boto.connect_ec2(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                       is_secure=True, region=region, port=8773, path='/services/Cloud', validate_certs=False)

# images = conn.get_all_images()
# for k in vars(images[0]).keys():
#        print("{0}".format(k))
#
# for i in images:
#     if (i.owner_id == '28eadf5ad64b42a4929b2fb7df99275c'):
#         print(i.name + ":" + i.id)

print(2.4)
res = conn.run_instances(image_id='ami-86f4a44c', key_name='newmbp', instance_type='m1.small',
                         placement='melbourne-qh2', min_count=2, max_count=2,
                            security_groups=['SSH','default'] )

for i in res.instances:
    print(i.id)
    vol = conn.create_volume(50,'melbourne-qh2')

    vol = conn.get_all_volumes([vol.id])[0]
    if vol.status == 'available':
        conn.attach_volume(vol.id, i.id, '/dev/vdc')
        print('Attached')
    else:
        print('Not available')

# print(ec2.meta.service_name)

# instances = ec2.create_instances(ImageId='ami-000007b9', MinCount=1, MaxCount=1, KeyName='newmbp', DryRun=True, InstanceType='t1.micro',
#                      SecurityGroupIds=['SSH','default'])
# print('2')
# instances = ec2.instances.filter(
#     Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
#

print('2')