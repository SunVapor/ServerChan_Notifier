"""
Server酱微信通知库
一个简单易用的Server酱通知封装，支持同步和异步发送微信通知
"""

import requests
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
import threading
from functools import wraps
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServerChanNotifier:
    """Server酱微信通知器"""
    
    def __init__(self, sendkey: str, default_channel: Optional[str] = None):
        """
        初始化Server酱通知器
        
        Args:
            sendkey: Server酱的SendKey
            default_channel: 默认的消息通道
        """
        self.sendkey = sendkey
        self.default_channel = default_channel
        self.api_url = f"https://sctapi.ftqq.com/{sendkey}.send"
        
    def send(
        self,
        title: str,
        desp: Optional[str] = None,
        short: Optional[str] = None,
        channel: Optional[str] = None,
        noip: bool = False,
        openid: Optional[str] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        发送Server酱通知
        
        Args:
            title: 消息标题（必填，最大32字符）
            desp: 消息内容（支持Markdown，最大32KB）
            short: 消息卡片内容（最大64字符）
            channel: 消息通道
            noip: 是否隐藏调用IP
            openid: 消息抄送的openid
            timeout: 请求超时时间（秒）
            
        Returns:
            dict: 包含推送结果的字典
        """
        # 构建请求数据
        payload = {
            "title": title[:32]  # 确保标题不超过32字符
        }
        
        if desp:
            payload["desp"] = desp
        if short:
            payload["short"] = short[:64]  # 确保short不超过64字符
        if channel:
            payload["channel"] = channel
        elif self.default_channel:
            payload["channel"] = self.default_channel
        if noip:
            payload["noip"] = "1"
        if openid:
            payload["openid"] = openid
        
        try:
            response = requests.post(
                self.api_url,
                data=payload,
                timeout=timeout,
                headers={'User-Agent': 'ServerChan-Python-SDK/1.0'},
                proxies={} 
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"Server酱通知发送成功。pushid: {result['data']['pushid']}")
            else:
                logger.warning(f"Server酱通知发送失败: {result.get('message')}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求错误: {e}")
            return {"code": -1, "message": f"网络请求错误: {e}"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return {"code": -1, "message": f"JSON解析错误: {e}"}
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return {"code": -1, "message": f"未知错误: {e}"}
    
    def send_async(
        self,
        title: str,
        desp: Optional[str] = None,
        **kwargs
    ) -> threading.Thread:
        """
        异步发送通知（非阻塞）
        
        Returns:
            threading.Thread: 异步线程对象
        """
        def async_send():
            self.send(title, desp, **kwargs)
        
        thread = threading.Thread(target=async_send)
        thread.daemon = True
        thread.start()
        return thread
    
    def notify_success(
        self,
        task_name: str,
        execution_time: Optional[float] = None,
        additional_info: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送成功通知模板
        
        Args:
            task_name: 任务名称
            execution_time: 执行时间（秒）
            additional_info: 附加信息
            
        Returns:
            dict: 推送结果
        """
        title = f"✅ {task_name} 执行成功"
        
        desp = f"""
## 🎉 任务执行成功

**任务名称**: {task_name}

**完成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        if execution_time is not None:
            desp += f"\n**执行时长**: {execution_time:.2f} 秒"
        
        if additional_info:
            desp += f"\n**详细信息**:\n{additional_info}"
            
        return self.send(title, desp, **kwargs)
    
    def notify_error(
        self,
        task_name: str,
        error_message: str,
        execution_time: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送错误通知模板
        
        Args:
            task_name: 任务名称
            error_message: 错误信息
            execution_time: 执行时间（秒）
            
        Returns:
            dict: 推送结果
        """
        title = f"❌ {task_name} 执行失败"
        
        desp = f"""
## ⚠️ 任务执行失败

**任务名称**: {task_name}

**失败时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**错误信息**: {error_message}
"""
        if execution_time is not None:
            desp += f"\n**执行时长**: {execution_time:.2f} 秒"
            
        return self.send(title, desp, **kwargs)
    
    def notify_completion(
        self,
        task_name: str,
        success: bool,
        execution_time: Optional[float] = None,
        message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送任务完成通知（自动判断成功/失败）
        
        Args:
            task_name: 任务名称
            success: 是否成功
            execution_time: 执行时间（秒）
            message: 附加消息
            
        Returns:
            dict: 推送结果
        """
        if success:
            return self.notify_success(task_name, execution_time, message, **kwargs)
        else:
            return self.notify_error(task_name, message or "未知错误", execution_time, **kwargs)

def task_notifier(sendkey: str, task_name: Optional[str] = None):
    """
    装饰器：自动为函数添加执行通知
    
    Args:
        sendkey: Server酱SendKey
        task_name: 任务名称（默认为函数名）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            notifier = ServerChanNotifier(sendkey)
            actual_task_name = task_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                notifier.notify_success(
                    actual_task_name,
                    execution_time,
                    f"函数 {func.__name__} 执行成功"
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                notifier.notify_error(
                    actual_task_name,
                    str(e),
                    execution_time
                )
                raise e
        return wrapper
    return decorator

# 全局实例（可选）
_global_notifier = None

def init_global_notifier(sendkey: str, default_channel: Optional[str] = None):
    """初始化全局通知器"""
    global _global_notifier
    _global_notifier = ServerChanNotifier(sendkey, default_channel)
    return _global_notifier

def get_global_notifier() -> ServerChanNotifier:
    """获取全局通知器"""
    if _global_notifier is None:
        raise ValueError("全局通知器未初始化，请先调用 init_global_notifier()")
    return _global_notifier

# 快捷函数
def quick_notify(sendkey: str, title: str, message: str = ""):
    """快速发送通知"""
    notifier = ServerChanNotifier(sendkey)
    return notifier.send(title, message)