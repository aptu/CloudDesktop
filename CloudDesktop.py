import argparse
import sys
import boto3
import os
# import botocore

DEFAULT_REGION='us-west-2'

class CloudDesktop:
    def __init__(self):
        self.__ec2 = boto3.client('ec2')
        self.__region = DEFAULT_REGION
        self.__dynamo = boto3.client('dynamodb', region_name=self.__region)
        self.__s3 = boto3.client('s3')
        self.__username = os.getlogin()
        
        self.__table_name = 'CloudDesktopTable'

    def __create_keypair(self):
        
        print("Logged user: " + self.__username)
        # The key-pair for each user saved in "Username.pm" file
        filename = self.__username + '.pem'
        try:
            keyfile = open(filename, 'r')
            print('KeyPair already exists')
        except IOError:
            keypair = self.__ec2.create_key_pair(KeyName=self.__username)
            with open(filename, 'w') as keyfile:
                keyfile.write(keypair['KeyMaterial'])
                print('KeyPair created')

    def __remove_keypair(self):
       
        response = self.__ec2.delete_key_pair(KeyName=self.__username)
        print(response)

    def config(self, args):
        self.__create_keypair()
        # self.create_dynamo(args)
        print("received args: %s" % args)
        self.write_dynamo(args)
        self.read_dynamo(args)

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


    def read_dynamo(self, args):
        pass

    def write_dynamo(self, args):
        params = {}
        params['Username'] = {'S':self.__username}
        params['VM'] = {'S': args.vm}
        params['Size'] = {'S':args.size}
        params['Packages'] = {'L': [ {'S': pkg} for pkg in args.pkgs.split(',')]}
        self.__dynamo.put_item(TableName=self.__table_name, Item=params) 
        




    def reset(self, args):
        self.__remove_keypair()
        pass

    def start(self, args):
        print(args)
        pass

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

    parser_start = subparsers.add_parser('start', help='Start work')
    parser_start.add_argument('--vm', dest='vm', help='VM to start')
    
    parser_reset = subparsers.add_parser('reset', help='Reset all configuration')
    args = parser.parse_args()
#    print(args)

    cloudesktop = CloudDesktop()

    getattr(cloudesktop, args.cmd)(args)



if __name__ == '__main__':
    main()
