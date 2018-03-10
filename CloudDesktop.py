import argparse
import sys

class CloudDesktop:
    def __init__(self):
        pass

    def config(self, args):
        pass

    def reset(self, args):
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
