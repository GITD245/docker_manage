import argparse
import random
import string
import yaml
import os
import configparser


def generate_random_string(length):
    """生成一个指定长度的随机字符串，包含大写字母、小写字母和数字。"""
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string


def make_yaml_data(args,config):
    yaml_data = {
        'image': config['DOCKERCOMPOSE']['IMAGE'],
        'ipc':'host',
        'container_name': args.user,
        'hostname': f'docker-{args.user}',
        'volumes': [f'/docker/{args.user}/workspace:/workspace', f'/docker/{args.user}/home:/home', f'/docker/data:/data'],
        'ports': [f'{args.port}:22'],
        'command': f"/bin/bash -c \"service ssh restart && echo 'root:{args.passwd}' | chpasswd && /bin/bash\"",
        'tty': True,
        'ulimits':{
            'memlock':{
                'soft': -1,
                'hard': -1
            }
        },
        'deploy': {
            'resources': {
                'reservations': {
                    'devices': [{
                        "driver": "nvidia",
                        'count': args.gpus,
                        'capabilities': ['gpu']
                    }]
                }
            }
        }
    }
    return yaml_data


def read_DockerComposefile():
    if not os.path.isfile('compose.yaml'):
        with open('compose.yaml', 'w') as file:
            print('No compose.yaml file found, generate compose.yaml')

    with open('compose.yaml', 'r') as file:
        yaml_data = yaml.full_load(file)
    return yaml_data


def write_DockerComposefile(docker_compose_file, yaml_data, args):
    if docker_compose_file is None:
        with open('compose.yaml', 'w') as file:
            yaml.dump({'services': {args.user: yaml_data}}, file)
    else:
        with open('compose.yaml', 'w') as file:
            docker_compose_file['services'][args.user] = yaml_data
            yaml.dump(docker_compose_file, file)


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', type=str, required=True, help="user name")
    parser.add_argument('--passwd', type=str, default=None, help="root passwd")
    parser.add_argument('--port', type=int, default=None, help="ssh port")
    parser.add_argument('--gpus', type=str, default='all', choices=[
                        '1', '2', '3', '4', '5', '6', '7', 'all'], help="Number of GPUs used")
    args = parser.parse_args()

    docker_compose_file = read_DockerComposefile()

    # if args.passwd is None, set a random passwd
    if args.passwd is None:
        args.passwd = generate_random_string(8)

    # if args.port is None, set args.port to Maximum port number already in use +1
    if args.port is None:
        if docker_compose_file is not None:
            ssh_port_list = []
            for user in docker_compose_file['services']:
                user_data = docker_compose_file['services'][user]
                ssh_port = int(user_data['ports'][0].split(':')[0])
                ssh_port_list.append(ssh_port)
            args.port = max(ssh_port_list)+1
        else:
            args.port = config['DOCKERCOMPOSE']['START_PROT']

    new_yaml_data = make_yaml_data(args,config)

    docker_compose_file = write_DockerComposefile(
        docker_compose_file, new_yaml_data, args)

    print(
        f"\ndocker name:{args.user}\n\nroot password:{args.passwd}\n\nssh:\nssh -p {args.port} root@{config['DOCKERCOMPOSE']['IP']}\n\nssh config example:\nHost {config['DOCKERCOMPOSE']['HOSTNAME']}\nHostName {config['DOCKERCOMPOSE']['IP']}\nUser root\nPort {args.port}\nProxyJump {config['DOCKERCOMPOSE']['PROXYJUMP']}\n")
    print('注意事项：')
    print('1. 数据集数据放到 /data 目录下，实验代码相关数据放到 /home 或 /workspace 这几个目录设置了数据持久化，如果容器出问题重置了，这些目录下的文件会保留，其他的目录下的文件大概率会丢失。')
    print('2. 定期备份数据与代码!!定期备份数据与代码!!定期备份数据与代码!!Linux 环境下数据丢失极难找回，且删除没有确认。')
    print('3. 尽量不要用完所有的显卡，以免其他人无法使用。如遇到时间紧张需要用卡的情况请联系设备管理员协调。')

if __name__ == '__main__':
    main()
