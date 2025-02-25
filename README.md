### Docker集群管理

**原始镜像：nvidia/pytorch:24.03-py3**

```bash
git clone https://github.com/GITD245/docker_manage.git
```

在config.ini中填写配置
```ini
[DOCKERFILE]
IMAGE = nvcr.io/nvidia/pytorch:24.03-py3 ;原始镜像
[DOCKERCOMPOSE]
DOCKERFILE_IMAGE = ngc:24.03 ;通过dockerfile创建的镜像名
HOST = name ;该容器的host 填写于ssh config Host
HOSTNAME = 127.0.0.1 ;宿主机IP 填写于ssh config HostName
PROXYJUMP = proxyjump ;跳板机 填写于ssh config ProxyJump
START_PORT = 40000 ;第一个用户的ssh映射端口
[PROXY]
PROXY = localhost ;代理地址 用于--localproxy选项
```

生成DockerFile文件
```bash
python make_dockerfile.py
```
注册nvcr.io账号并获取API
https://org.ngc.nvidia.com/setup/api-key

登陆NGC nvcr.io
```bash
docker login nvcr.io
```

使用DockerFile文件创建镜像
```bash
docker build -t ngc:24.03 .
```
生成compose.yaml文件 需指定用户名 运行后会容器输出连接容器的相关命令及注意事项
```bash
python generate_dockercompose.py --user username #可使用--network 指定网络模式（host 或者 bridge） --delete 删除用户 --localproxy 使用宿主机7890端口作为代理
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