### Docker集群管理

**原始镜像：nvidia/pytorch:24.02-py3**

在config文件夹中填写配置

生成DockerFile文件
```bash
python generate_dockerfile.py
```
使用DockerFile文件创建镜像
```bash
docker build -t ngc:24.02 .
```
生成compose.yaml文件 运行后会容器输出连接容器的相关命令及注意事项
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