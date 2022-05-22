# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import datetime
from typing import Dict, List

from config import appid, token
from redis_handle import RedisConn
import qqbot

from qqbot.model.message import (
    MessageArk, MessageArkKv, MessageArkObj, MessageArkObjKv
)

public_channel_id = ""
redisConn = RedisConn()


async def _message_handler(event, message: qqbot.Message):
    """
    定义事件回调的处理

    :param event: 事件类型
    :param message: 事件对象（如监听消息是Message对象）
    """
    msg_api = qqbot.AsyncMessageAPI(t_token, False)
    # 打印返回信息
    content = message.content
    qqbot.logger.info("event %s" % event + ",receive message %s" % content)
    # 根据指令触发不同的推送消息
    if "/打卡 " in content:
        punch = get_punch(message)
        if punch['is_correct_format'] == 1:
            await _send_punch_ark_message(punch, message.channel_id, message.id)
        else:
            # 用户发送的日期格式有误，进行提醒
            await _send_punch_err_message(punch, message.channel_id, message.id)


async def _create_punch_err_ark_obj_list(punch_err_dict) -> List[MessageArkObj]:
    obj_list = [MessageArkObj(obj_kv=[MessageArkObjKv(key="desc", value="用户" + punch_err_dict['result']['username'] + "日期格式有误！")]),
                MessageArkObj(obj_kv=[MessageArkObjKv(key="desc", value="日期格式：yyyy-mm-dd（2022-05-06）")])]
    return obj_list


async def _send_punch_err_message(punch_err_dict, channel_id, message_id):
    """
    被动回复-子频道发送打卡格式有误消息
    :param punch_err_dict: 打卡有误消息
    :return:
    """
    # 构造消息发送请求数据对象
    ark = MessageArk()
    # 模板ID=23
    ark.template_id = 23
    ark.kv = [MessageArkKv(key="#DESC#", value="描述"),
              MessageArkKv(key="#PROMPT#", value="提示消息"),
              MessageArkKv(key="#LIST#", obj=await _create_punch_err_ark_obj_list(punch_err_dict))]
    # 通过api发送回复消息
    send = qqbot.MessageSendRequest(content="", ark=ark, msg_id=message_id)
    msg_api = qqbot.AsyncMessageAPI(t_token, False)
    await msg_api.post_message(channel_id, send)


async def _create_punch_ark_obj_list(punch_dict) -> List[MessageArkObj]:
    obj_list = [MessageArkObj(obj_kv=[MessageArkObjKv(key="desc",
                                                      value="用户" + punch_dict['result']['username'] + ("打卡成功！" if
                                                                                                        punch_dict[
                                                                                                            'result'][
                                                                                                            'have_signed'] == 0 else "已经打卡过了～"))]),
                MessageArkObj(obj_kv=[MessageArkObjKv(key="desc", value="打卡日期：" + punch_dict['result']['datetime'])]),
                MessageArkObj(
                    obj_kv=[MessageArkObjKv(key="desc", value="当月打卡天数：" + str(punch_dict['result']['sign_count']))]),
                MessageArkObj(
                    obj_kv=[MessageArkObjKv(key="desc",
                                            value="已连续打卡天数：" + str(punch_dict['result']['continuous_sign_count']))])
                ]
    return obj_list


async def _send_punch_ark_message(punch_dict, channel_id, message_id):
    """
    被动回复-子频道发送打卡消息
    :param punch_dict: 打卡消息
    :param channel_id: 回复消息的子频道ID
    :param message_id: 回复消息ID
    :return:
    """
    # 构造消息发送请求数据对象
    ark = MessageArk()
    # 模板ID=23
    ark.template_id = 23
    ark.kv = [MessageArkKv(key="#DESC#", value="描述"),
              MessageArkKv(key="#PROMPT#", value="提示消息"),
              MessageArkKv(key="#LIST#", obj=await _create_punch_ark_obj_list(punch_dict))]
    # 通过api发送回复消息
    send = qqbot.MessageSendRequest(content="", ark=ark, msg_id=message_id)
    msg_api = qqbot.AsyncMessageAPI(t_token, False)
    await msg_api.post_message(channel_id, send)


# 判断一个字符串是否是yyyy-mm-dd格式的
def validate(date_text):
    try:
        if date_text != datetime.datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        return 1
    except ValueError:
        return 0


def get_punch(message: qqbot.Message) -> Dict:
    """
    获取用户打卡数据

    :message: 用户发送/打卡 后收到的消息
    :return: 返回打卡数据的json对象
    返回示例
    {
        is_correct_format: 1, # 表示day是否是合法的字符串
        raw_str : "2022-5-21", # 用户发送的原始字符串，用于错误处理
        result: {
            username: "mahler",
            have_signed: 1, # 今天是否已经打卡
            datetime: "2022-5-21",
            sign_count: 12, # 本月打卡次数
            continuous_sign_count: 23, # 连续打卡次数
        }
    }
    """
    raw_str = message.content.split("/打卡 ")[1]
    is_correct_format = validate(raw_str)
    username = message.author.username
    uid = message.author.id
    if is_correct_format == 0:
        result = {'username': username}
    else:
        day = datetime.datetime.strptime(raw_str, '%Y-%m-%d')
        have_signed = redisConn.check_sign(uid, day)
        if have_signed == 0:
            redisConn.do_sign(uid, day)
        result = {
            'username': username,
            'have_signed': have_signed,
            'datetime': raw_str,
            'sign_count': redisConn.get_sign_count(uid, day),
            'continuous_sign_count': redisConn.get_continuous_sign_count(uid, day)
        }

    punch_dict = {
        'is_correct_format': is_correct_format,
        'raw_str': raw_str,
        'result': result
    }
    return punch_dict


if __name__ == "__main__":
    # async的异步接口的使用示例
    t_token = qqbot.Token(appid, token)
    qqbot_handler = qqbot.Handler(qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler)
    qqbot.async_listen_events(t_token, False, qqbot_handler)
    print("hello")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
