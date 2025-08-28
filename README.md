# ServerChan Notifier

一个简单易用的Server酱微信通知库。

## 安装

```bash
pip install git+https://github.com/SunVapor/ServerChan_Notifier.git
```

## 快速开始

你首先需要在https://sct.ftqq.com/上获取SENDKEY

```python
from serverchan_notifier import ServerChanNotifier

# 初始化通知器
notifier = ServerChanNotifier("你的SENDKEY")

# 发送简单通知
notifier.send("任务完成", "Python脚本执行成功！")

# 使用模板方法，添加任务用时
notifier.notify_success("数据处理任务", 120.5, "处理了1000条数据")

# 异步发送（不阻塞主线程）
notifier.send_async("异步通知", "这是在后台发送的通知")
```

## 高级用法

### 使用装饰器自动通知

```python
from serverchan_notifier import task_notifier

@task_notifier("你的SENDKEY", "重要任务")
def important_task():
    # 你的任务代码
    pass
```

### 全局通知器

```python
from serverchan_notifier import init_global_notifier, get_global_notifier

# 初始化全局通知器
init_global_notifier("你的SENDKEY")

# 在任何地方使用
get_global_notifier().send("全局通知", "来自任何地方的消息")
```
