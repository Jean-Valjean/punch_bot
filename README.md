# punch_bot
基于redis+qqbot sdk的QQ频道打卡机器人

### 使用说明
将config.py中的appid和token以及redis的host和port改成自己的，然后运行main函数即可

## 项目结构
### redis_handle.py
<ol>
  <li>提供与redis交互的接口</li>
  <li>用户的打卡记录按月存储在bitmap中，key命名格式为uid:yyyy:mm</li>
  <li>提供方法用于查看/获取：
    <ol>
      <li>检查用户当天是否已经打卡</li>
      <li>签到，将数据写入bitmap</li>
      <li>获取当月总打卡天数</li>
      <li>获取连续打卡天数</li>
    </ol>
  </li>
</ol>

### main.py
提供方法用于构造消息json数据、构造ark消息、发送ark消息
<ol>
  <li>_message_handler：用于处理“at机器人消息”，根据用户调用的功能作出响应（目前只提供“/打卡”功能）</li>
  <li>打卡功能提供简单的差错处理，检验用户发送的日期格式，不正确则发出响应提示</li>
  <li>validate(data_text)：用于判断用户发送过来的日期是否是yyyy-mm-dd，不是则需要进行打卡出错处理</li>
  <li>get_punch：根据用户发送过来的打卡消息构造json对象，用于后续ark_obj的构造，用于打卡/差错处理</li>
  <li>打卡处理：用户发送了正确的打卡格式，有以下方法用于处理该任务
    <ol>
      <li>_create_punch_ark_obj_list(punch_dict)：使用get_punch返回的json数据，构造ark.kv</li>
      <li>_send_punch_ark_message()：构造ark消息后发送给用户</li>
    </ol>
  </li>
  <li>打卡出错处理：用户发送了错误的打卡格式，有以下方法用于处理该任务
    <ol>
      <li>_create_punch_err_ark_obj_list(punch_dict)：使用get_punch返回的json数据，构造ark.kv</li>
      <li>_send_punch_err_ark_message()：构造ark消息后发送给用户</li>
    </ol>
  </li>
</ol>
