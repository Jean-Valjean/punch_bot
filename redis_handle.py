import redis
import datetime

from config import host, port


def get_key(uid: str, day: datetime.datetime):
    """
    用bitmap存放用户每个月的前导信息，key的格式为 uid:yyyymm
    :param uid:
    :param day:
    :return: key
    """
    key = uid + ':' + str(day.year) + str(day.month)
    return key


def get_offset(day: datetime.datetime):
    """
    计算bitmap的位置
    :param day:
    :return:
    """
    return day.day - 1


class RedisConn:
    # 创建redis连接
    r = redis.Redis(host=host, port=port, decode_responses=True)

    def do_sign(self, uid, day):
        """
        为uid签到
        :param uid:
        :param day:
        :return:
        """
        key = get_key(uid, day)
        offset = get_offset(day)
        self.r.setbit(key, offset, 1)

    def check_sign(self, uid, day):
        """
        查看uid在day是否已签到
        :param uid:
        :param day:
        :return: 1 or 0
        """
        key = get_key(uid, day)
        offset = get_offset(day)
        return 1 if self.r.getbit(key, offset) == 1 else 0

    def get_sign_count(self, uid, day: datetime.datetime):
        """
        获取用户在该月签到次数
        :param day:
        :param uid:
        :return:
        """
        key = get_key(uid, day)
        return self.r.bitcount(key)

    def get_continuous_sign_count(self, uid, day: datetime.datetime):
        """
        获取用户当前连续签到次数
        :param uid:
        :param day:
        :return:
        """
        count = 0
        step = datetime.timedelta(days=1)
        while self.check_sign(uid, day):
            count += 1
            day = day - step
        return count
