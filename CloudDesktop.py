import argparse
import sys
import boto3
import os

class CloudDesktop:
    def __init__(self):
        self.__ec2 = boto3.client('ec2')
        pass

    def __create_keypair(self):
        username = os.getlogin()
        print("Logged user: " + username)
        # The key-pair for each user saved in "Username.pm" file
        filename = username + '.pem'
        try:
            keyfile = open(filename, 'r')
            print('KeyPair already exists')
        except IOError:
            keypair = self.__ec2.create_key_pair(KeyName=username)
            with open(filename, 'w') as keyfile:
                keyfile.write(keypair['KeyMaterial'])
                print('KeyPair created')

    def __remove_keypair(self):
        username = os.getlogin()
        response = self.__ec2.delete_key_pair(KeyName=username)
        print(response)

    def config(self, args):
        self.__create_keypair()
        pass


    def reset(self, args):
        self.__remove_keypair()
        pass

    def start(self, args):
        print(args)
        pass

    def list(self, args):
        pass

def main():
    parser = argparse.ArgumentParser(description="Choose action")
    subparsers = parser.add_subparsers(help='commands', dest='cmd')

    parser_config = subparsers.add_parser('config', help='Configure cloud desktop')
#    parser_config.add_argument('--config', dest='config', help='Configure usage')
#    parser.add_argument('--start', dest='start', description=)


    parser_start = subparsers.add_parser('start', help='Start work')
    parser_start.add_argument('--vm', dest='vm', help='VM to start')

    parser_reset = subparsers.add_parser('reset', help='Reset all configuration')
    args = parser.parse_args()
#    print(args)

    cloudesktop = CloudDesktop()

    getattr(cloudesktop, args.cmd)(args)



if __name__ == '__main__':
    main()
