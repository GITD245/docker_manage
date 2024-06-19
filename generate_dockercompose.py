import argparse
import random
import string
import yaml
import os
import sys
import configparser
import subprocess
from copy import deepcopy


def generate_random_string(length):
    """生成一个指定长度的随机字符串，包含大写字母、小写字母和数字。"""
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string


def make_yaml_data(args, config):
    yaml_data = {
        'image': config['DOCKERCOMPOSE']['DOCKERFILE_IMAGE'],
        'ipc': 'host',
        'container_name': args.user,
        'network_mode': args.network,
        'hostname': f'docker-{args.user}',
        'volumes': [f'/docker/{args.user}/workspace:/workspace', f'/docker/{args.user}/home:/home', f'/docker/data:/data'],
        'command': f"/bin/bash -c \"service ssh restart && echo 'root:{args.passwd}' | chpasswd && /bin/bash\"",
        'restart': 'unless-stopped',
        'tty': True,
        'ulimits': {
            'memlock': {
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
    if args.network=='bridge':
        yaml_data['ports']=[f'{args.port}:22']
    elif args.network=='host':
        yaml_data['command']=f"/bin/bash -c \"service ssh restart && sed -i 's/#Port 22/Port {args.port}/' /etc/ssh/sshd_config && service ssh restart && echo 'root:{args.passwd}' | chpasswd && /bin/bash\""
    return yaml_data


def read_DockerComposefile():
    if not os.path.isfile('compose.yaml'):
        with open('compose.yaml', 'w') as file:
            print('没有compose.yaml文件, 自动创建compose.yaml')
            yaml.safe_dump({'services': {}}, file)

    with open('compose.yaml', 'r') as file:
        yaml_data = yaml.safe_load(file)
        if yaml_data['services']=={}:
            yaml_data=None
    return yaml_data


def write_DockerComposefile(docker_compose_file, yaml_data, args):
    if docker_compose_file is None:
        with open('compose.yaml', 'w') as file:
            yaml.safe_dump({'services': {args.user: yaml_data}}, file)
    else:
        with open('compose.yaml', 'w') as file:
            docker_compose_file['services'][args.user] = yaml_data
            yaml.safe_dump(docker_compose_file,file)


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', type=str, required=True, help="user name")
    parser.add_argument('--passwd', type=str, default=None, help="root passwd")
    parser.add_argument('--port', type=int, default=None, help="ssh port")
    parser.add_argument('--network', type=str, choices=['host','bridge'],default='bridge',help="network mode")
    parser.add_argument('--delete', action='store_true', help="delete user")
    parser.add_argument('--gpus', type=str, default='all', choices=[
                        '1', '2', '3', '4', '5', '6', '7', 'all'], help="Number of GPUs used")
    args = parser.parse_args()

    docker_compose_file = read_DockerComposefile()

    if args.delete:
        if args.user in docker_compose_file['services']:
            del docker_compose_file['services'][args.user]
            print(f'删除用户 {args.user}')
            with open('compose.yaml', 'w') as file:
                yaml.safe_dump(docker_compose_file, file, default_flow_style=False, allow_unicode=True)
        else:
            print(f'没有该用户')
        sys.exit()
    
    # if args.passwd is None, set a random passwd
    if args.passwd is None:
        args.passwd = generate_random_string(8)

    # if args.port is None, set args.port to Maximum port number already in use +1
    if args.port is None:
        if docker_compose_file is not None:
            ssh_port_list = []
            for user in docker_compose_file['services']:
                user_data = docker_compose_file['services'][user]
                if 'ports' in user_data:
                    ssh_port = int(user_data['ports'][0].split(':')[0])
                else:
                    ssh_port = int(user_data['command'].split('Port')[2].split('/')[0])
                ssh_port_list.append(ssh_port)
            args.port = max(ssh_port_list)+1
        else:
            args.port = config['DOCKERCOMPOSE']['START_PORT']

    new_yaml_data = make_yaml_data(args, config)

    docker_compose_file = write_DockerComposefile(
        docker_compose_file, new_yaml_data, args)

    print(
        f"\ndocker name:\n{args.user}\n\nroot password:\n{args.passwd}\n\nssh:\nssh -p {args.port} root@{config['DOCKERCOMPOSE']['IP']}\n\nssh config example:\nHost {config['DOCKERCOMPOSE']['HOSTNAME']}\nHostName {config['DOCKERCOMPOSE']['IP']}\nUser root\nPort {args.port}\nProxyJump {config['DOCKERCOMPOSE']['PROXYJUMP']}\n")
    print('注意事项：')
    print('1. 数据集数据放到 /data 目录下，实验代码相关数据放到 /home 或 /workspace; 这几个目录设置了数据持久化，如果容器出问题重置了，这些目录下的文件会保留，其他的目录下的文件大概率会丢失。')
    print('#### /root 目录未设置数据持久化!!! ####')
    print('2. 定期备份数据与代码!!定期备份数据与代码!!定期备份数据与代码!!Linux 环境下数据丢失极难找回，且删除没有确认。')
    print('3. 尽量不要用完所有的显卡，以免其他人无法使用。如遇到时间紧张需要用卡的情况请联系设备管理员协调。')
    print('4. 尽量直接使用root用户运行。新建用户也不要超过一个。')
    print(f"5. 正在使用{args.network}网络模式")
    print(f"6. 正在使用的镜像: {config['DOCKERCOMPOSE']['DOCKERFILE_IMAGE']}")
    subprocess.run("cp compose.yaml compose.yaml.backup", shell=True, capture_output=True, text=True)


if __name__ == '__main__':
    main()