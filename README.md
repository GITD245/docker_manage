### Docker集群管理

**原始镜像：nvidia/pytorch:24.02-py3**

```bash
git clone https://github.com/GITD245/docker_manage.git
```

在config.ini中填写配置
```ini
[DOCKERFILE]
IMAGE = nvcr.io/nvidia/pytorch:24.03-py3 ;原始镜像
[DOCKERCOMPOSE]
DOCKERFILE_IMAGE = ngc:24.02 ;通过dockerfile创建的镜像名
IP = 127.0.0.1 ;宿主机IP
HOSTNAME = hostname ;宿主机hostname 用于生成ssh config
PROXYJUMP = proxyjump ;跳板机 用于生成ssh config
START_PORT = 40000 ;第一个用户的ssh映射端口
```

生成DockerFile文件
```bash
python generate_dockerfile.py
```
使用DockerFile文件创建镜像
```bash
docker build -t ngc:24.02 .
```
生成compose.yaml文件 需指定用户名 运行后会容器输出连接容器的相关命令及注意事项
```bash
python generate_dockercompose.py --user username
```
创建容器
```bash
docker compose create
```
启动容器
```bash
docker compose start
```
**建议直接使用docker内root用户，在docker内新建用户会因为容器与宿主机使用同一usernamespace而导致用户映射出问题**