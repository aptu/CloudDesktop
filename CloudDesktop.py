import argparse
import sys
import boto3
import os
import subprocess
import time

# import botocore

DEFAULT_REGION = 'us-west-2'
DEFAULT_PACKAGES = ['xauth', 'awscli']
DEFAULT_AMI = 'ami-79873901' #'ami-f2d3638a'
DEFAULT_USER = 'ubuntu' # 'ec2-user'

S3_UPLOADER_KEY_ID = 'AKIAJPCBYEIQEJB67TDA'
S3_UPLOADER_SECRET_KEY = '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'

class CloudDesktop:
    def __init__(self):
        self.__ec2 = boto3.client('ec2')
        self.__region = DEFAULT_REGION
        self.__dynamo = boto3.client('dynamodb', region_name=self.__region)
        self.__s3 = boto3.client('s3')
        self.__username = os.getlogin()        
        self.__table_name = 'CloudDesktopTable'
        self.__key_filename = self.__username + '.pem'

    def __create_keypair(self):        
        print("Logged user: " + self.__username)
        # The key-pair for each user saved in "Username.pm" file
        try:
            keyfile = open(self.__key_filename, 'r')
            print('KeyPair already exists')
        except IOError:
            keypair = self.__ec2.create_key_pair(KeyName=self.__username)
            with open(self.__key_filename, 'w') as keyfile:
                keyfile.write(keypair['KeyMaterial'])
                os.chmod(self.__key_filename, 0o600)
                print('KeyPair created')

    def __remove_keypair(self):       
        response = self.__ec2.delete_key_pair(KeyName=self.__username)
        print(response)
        os.remove(self.__key_filename)

    def config(self, args):
        self.__create_keypair()
        # self.create_dynamo(args)
        print("received args: %s" % args)
        self.write_dynamo(args)
        # self.read_dynamo(args.vm)

        pass

    def create_dynamo(self, args):
        try:
            table = self.__dynamo.create_table(TableName=self.__table_name, 
                    KeySchema=[
                        {'AttributeName' : 'Username', 'KeyType' : 'HASH'},
                        {'AttributeName': 'VM', 'KeyType' : 'RANGE'}
                        ],
                    AttributeDefinitions=[
                        {'AttributeName' : 'Username', 'AttributeType' : 'S'}, 
                        {'AttributeName' : 'VM', 'AttributeType' : 'S'}
                        ],
                    ProvisionedThroughput={'ReadCapacityUnits' : 1, 'WriteCapacityUnits' : 1})

            # wait until the table exists
            boto3.resource('dynamodb', region_name=self.__region).Table(self.__table_name).wait_until_exists()
        # except self.__dynamo.exceptions.TableAlreadyExistsException:
        except:
            print('Table already exists')


    # read by VMname
    def __read_dynamo(self, vmname):
        key_expr = '(Username = :n) AND (VM = :vm)'
        expr_attr = {':n' : {'S': self.__username}, ':vm' : {'S':vmname}}
        queryResult = self.__dynamo.query(TableName=self.__table_name, Select='ALL_ATTRIBUTES',
        KeyConditionExpression=key_expr, 
        ExpressionAttributeValues=expr_attr)

        print("Query results: %s" %queryResult['Items'])
        return queryResult['Items'][0]
        


    def write_dynamo(self, args):
        params = {}
        params['Username'] = {'S':self.__username}
        params['VM'] = {'S': args.vm}
        params['Size'] = {'S':args.size}
        params['Packages'] = {'L': [ {'S': pkg} for pkg in DEFAULT_PACKAGES + args.pkgs.split(',')]}
        self.__dynamo.put_item(TableName=self.__table_name, Item=params) 
        

    def __find_ec2_instance(self, vmname):
        response = self.__ec2.describe_instances(Filters=[{'Name': 'key-name',
        'Values' : [self.__username]}], MaxResults=100)
        #print(response)
        tagMatch = lambda x: {'Key' : 'Name', 'Value' : vmname} in x['Tags'] and x['State']['Name'] == 'running'
        for reservation in response['Reservations']:
            match = list(filter(tagMatch, reservation['Instances']))
            if len(match) > 0:
                print("Found description of %s: %s" % (vmname, match))
                return match[0]
        return None

    def __install_packages(self, vmname, vmconfig):
        vmdesc = self.__find_ec2_instance(vmname)
        public_ip = vmdesc['PublicDnsName']
        pkgs_to_install = [ p['S'] for p in vmconfig['Packages']['L']]
        print("Installing packages %s in %s" % (pkgs_to_install, vmname))
        remote_cmd = ['ssh', '-i', self.__key_filename, '-o', 'StrictHostKeyChecking=no', DEFAULT_USER + '@' + public_ip]
        subprocess.call(remote_cmd + ['sudo', 'apt-get', 'update'])
        # cmd = ['ssh', '-i', self.__key_filename, 'ec2-user@'+public_ip, 'sudo', 'yum', 'install', '-y'] + pkgs_to_install
        cmd = remote_cmd + ['sudo', 'apt-get', 'install', '-y'] + pkgs_to_install
        print(cmd)
        subprocess.call(cmd)

        # configure s3 uploader
        subprocess.call(remote_cmd + ['mkdir', '~/Documents', '~/.aws'])
        subprocess.call(remote_cmd + [ '(', 'echo', S3_UPLOADER_KEY_ID, ';', 'echo', S3_UPLOADER_SECRET_KEY, ';', 'echo', self.__region, ';', 'echo', '\'', '\'', ')', '|', 'aws', 'configure'])


    def reset(self, args):
        self.__remove_keypair()
        pass

    def start(self, args):
        print("Starting VM %s" % args.vm)
        print(args)

        if not self.__find_ec2_instance(args.vm) is None:
            print("VM %s is already running." % args.vm)
            return

        vmconfig = self.__read_dynamo(args.vm)

        params = {} 
        params['ImageId'] = DEFAULT_AMI
        params['InstanceType'] = vmconfig['Size']['S']
        params['KeyName'] = self.__username
        params['MinCount'] = 1
        params['MaxCount'] = 1
        params['TagSpecifications'] = [{'ResourceType': 'instance',
        'Tags': [{'Key' : 'Name', 'Value' :args.vm}]}]
        launch_result = self.__ec2.run_instances(**params)

        print("Waiting for VM to start...")
        time.sleep(40)
        self.__install_packages(args.vm, vmconfig)

    def stop(self, args):
        print("Stopping VM %s" % args.vm)
        vmdesc = self.__find_ec2_instance(args.vm)
        if vmdesc is None:
            print("VM %s is already stopped." % args.vm)
            return

        public_ip = vmdesc['PublicDnsName']
        s3_prefix = "s3://css490storage/%s/%s/" % (self.__username, args.vm)
        remote_cmd = ['ssh', '-i', self.__key_filename, DEFAULT_USER + '@' + public_ip]
        subprocess.call(remote_cmd + ['ls', 'Documents/', '|', 'xargs', '-l', '-I{}', 'aws', 's3', 'cp', 'Documents/{}', s3_prefix + '{}'])
            # boto3.resource('s3').Bucket('cc490at_gaming').put_object(Key='test.txt', Body=open('test.txt', 'rb'))

        response = self.__ec2.terminate_instances(InstanceIds=[vmdesc['InstanceId']])
        

    def connect(self, args):
        self.start(args)
        vmname = args.vm
        vmdesc = self.__find_ec2_instance(vmname)
        public_ip = vmdesc['PublicDnsName']
        print("Connecting to %s" % vmname)
        cmd = ['ssh', '-i', self.__key_filename, '-XY', DEFAULT_USER+'@'+public_ip]
        print(cmd)
        subprocess.call(cmd)
        

    def listAll(self, args):
        pass

def main():
    parser = argparse.ArgumentParser(description="Choose action")
    subparsers = parser.add_subparsers(help='commands', dest='cmd')

    parser_config = subparsers.add_parser('config', help='Configure cloud desktop')
#    parser_config.add_argument('--config', dest='config', help='Configure usage')
#    parser.add_argument('--start', dest='start', description=)
    parser_config.add_argument('--vm',dest='vm', help='Type of vm: office, gaming, browser' )
    parser_config.add_argument('--size', dest='size', help='Size of vm')
    parser_config.add_argument('--pkgs', dest='pkgs', help='Packages to install on vm')

    parser_start = subparsers.add_parser('start', help='Start vm')
    parser_start.add_argument('--vm', dest='vm', help='VM to start')

    parser_stop = subparsers.add_parser('stop', help='Stop vm')
    parser_stop.add_argument('--vm', dest='vm', help='VM to stop')

    parser_connect = subparsers.add_parser('connect', help='Connect to vm')
    parser_connect.add_argument('--vm', dest='vm', help='VM to connect')
    
    parser_reset = subparsers.add_parser('reset', help='Reset all configuration')
    args = parser.parse_args()
#    print(args)

    cloudesktop = CloudDesktop()

    getattr(cloudesktop, args.cmd)(args)



if __name__ == '__main__':
    main()
