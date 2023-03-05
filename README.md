<img width="200" alt="截屏2023-03-03 13 59 46" src="https://user-images.githubusercontent.com/51039745/222689546-7612df0e-e28b-4693-9f5f-4ef2be3daf48.png">

# 川虎 ChatGPT
为ChatGPT API提供了一个Web图形界面。

基于 https://github.com/GaiZhenbiao/ChuanhuChatGPT 进行扩展。感谢原作者的优秀项目。

GUI for ChatGPT API
<img width="1204" alt="截屏2023-03-03 13 59 46" src="https://user-images.githubusercontent.com/51039745/222643242-c0b90a54-8f07-4fb6-b88e-ef338fd80f49.png">

## 安装方式

- 在环境变量中，加入 OPENAI_API_KEY 这个变量，值为 openai 的 api key：

```
export OPENAI_API_KEY=xxxxxx
```

- 安装依赖

```
pip install -r requirements.txt
```

如果报错，试试

```
pip3 install -r requirements.txt
```

如果还是不行，请先[安装Python](https://www.runoob.com/python/python-install.html)。

如果下载慢，建议[配置清华源](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)，或者科学上网。

- 启动

```
python3 ChuanhuChatbot.py
```

详细启动命令支持的参数，可通过

```shell
python3 ChuanhuChatbot.py --help
```

获取

## 使用技巧

- 使用System Prompt可以很有效地设定前提条件
- 对于长对话，可以使用“优化Tokens”按钮减少Tokens占用。
