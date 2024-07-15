import argparse
import random
import string
import configparser


def generate_random_string(length):
    """生成一个指定长度的随机字符串，包含大写字母、小写字母和数字。"""
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string


def make_DockerFile(args, config):
    # 基础配置
    command = f"FROM {config['DOCKERFILE']['IMAGE']}\nRUN mkdir /data\nRUN sed -i 's@//.*archive.ubuntu.com@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list\nRUN apt update\nRUN apt-get install -y --no-install-recommends openssh-server build-essential tmux net-tools sudo iproute2\nRUN mkdir /var/run/sshd\nRUN chmod 0755 /var/run/sshd\nRUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config\nRUN sed -i 's#PATH=.*#PATH=\"/usr/local/nvm/versions/node/v16.20.2/bin:/usr/local/lib/python3.10/dist-packages/torch_tensorrt/bin:/usr/local/mpi/bin:/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/ucx/bin:/opt/tensorrt/bin:/snap/bin\"#g' /etc/environment\nRUN sed -i 's/#force_color_prompt=yes/force_color_prompt=yes/' /root/.bashrc\nEXPOSE 22\n\n"

    if args.user is not None:
        # 生成用户 更改密码 加入sudo组
        command += f"RUN useradd -m -s /bin/bash {args.user} && echo '{args.user}:{args.passwd}' | chpasswd\nRUN usermod -aG sudo {args.user}\n\nUSER {args.user}\n"
        # 界面优化
        command += f"RUN sed -i 's/#force_color_prompt=yes/force_color_prompt=yes/g' /home/{args.user}/.bashrc\nRUN sudo sed -i 's/PS1=.*$/PS1=\"\\n\\[\\033[35m\\][\\\\t]\\[\\033[00m\\] \\[\\033[36m\\]\\u@\\h\\[\\033[00m\\] [\\w]\\n\\[\\033[34m\\]->\\[\\033[00m\\] \"/g' /home/{args.user}/.bashrc\n\n"
        # 配置conda
        command += f"RUN wget --quiet https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /home/{args.user}/miniconda.sh && /bin/bash /home/{args.user}/miniconda.sh -b -p /home/{args.user}/miniconda3 && echo \". /home/{args.user}/miniconda3/etc/profile.d/conda.sh\" >> /home/{args.user}/.bashrc && echo \"conda activate base\" >> /home/{args.user}/.bashrc\n\n"
        # 端口监听 设置工作目录
        command += f"WORKDIR /home/{args.user}"
    with open('Dockerfile', 'w') as dockerfile:
        dockerfile.write(command)


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpus', type=str, default='all')
    parser.add_argument('--user', type=str, default=None)
    parser.add_argument('--passwd', type=str, default=None)
    args = parser.parse_args()

    if args.passwd is None and args.user is not None:
        args.passwd = generate_random_string(14)
        print(f'the root passwd is {args.passwd}')

    make_DockerFile(args, config)


if __name__ == '__main__':
    main()
