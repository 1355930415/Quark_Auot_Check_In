import os
import re
import sys
import requests

# 替代 notify 功能
def send(title, message):
    print(f"{title}: {message}")

# 获取环境变量
def get_env():
    if "COOKIE_QUARK" in os.environ:
        cookie_str = os.environ.get("COOKIE_QUARK")
        cookie_list = re.split(r'\n|&&', cookie_str)
        cookie_list = [cookie.strip() for cookie in cookie_list if cookie.strip()]
        return cookie_list
    else:
        print('❌未添加COOKIE_QUARK变量')
        send('夸克自动签到', '❌未添加COOKIE_QUARK变量')
        sys.exit(0)

class Quark:
    def __init__(self, user_data):
        self.param = user_data

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        try:
            response = requests.get(url=url, params=querystring, timeout=10).json()
            if response.get("data"):
                return response["data"]
            else:
                print(f"❌ API 返回错误: {response.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        try:
            response = requests.post(url=url, json=data, params=querystring, timeout=10).json()
            if response.get("data"):
                return True, response["data"]["sign_daily_reward"]
            else:
                return False, response.get("message", "未知错误")
        except Exception as e:
            return False, str(e)

    def do_sign(self):
        log = ""
        user = self.param.get('user', '未知用户')

        growth_info = self.get_growth_info()

        if not growth_info:
            log += f"❌ 账号 [{user}] 签到异常：获取成长信息失败，请检查 cookie 是否失效\n"
            return log, False  # 返回 (log, success)

        log += (
            f" {'88VIP' if growth_info['88VIP'] else '普通用户'} [{user}]\n"
            f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}，"
            f"签到累计容量："
        )
        if "sign_reward" in growth_info['cap_composition']:
            log += f"{self.convert_bytes(growth_info['cap_composition']['sign_reward'])}\n"
        else:
            log += "0 MB\n"

        if growth_info["cap_sign"]["sign_daily"]:
            log += (
                f"✅ 签到日志: 今日已签到+{self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])}，"
                f"连签进度({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})\n"
            )
        else:
            sign, sign_return = self.get_growth_sign()
            if sign:
                log += (
                    f"✅ 执行签到: 今日签到+{self.convert_bytes(sign_return)}，"
                    f"连签进度({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})\n"
                )
            else:
                log += f"❌ 签到失败: {sign_return}\n"

        return log, True  # 成功


def main():
    msg = ""
    cookie_list = get_env()

    if not cookie_list:
        print("❌ COOKIE_QUARK 为空，无有效账号。")
        send('夸克自动签到', '❌ COOKIE_QUARK 为空，无有效账号。')
        sys.exit(0)

    print("✅ 检测到共", len(cookie_list), "个夸克账号\n")

    success_count = 0  # 成功签到的账号数
    total_count = len(cookie_list)

    for i, cookie in enumerate(cookie_list):
        user_data = {}
        for item in cookie.replace(" ", "").split(';'):
            if '=' in item:
                key, value = item.split('=', 1)
                user_data[key] = value

        if 'user' not in user_data:
            user_data['user'] = f"账号{i+1}"

        print(f"🙍🏻‍♂️ 开始处理第 {i+1} 个账号 [{user_data['user']}]")
        try:
            quark = Quark(user_data)
            log, success = quark.do_sign()
            if success:
                success_count += 1
        except Exception as e:
            log = f"❌ 账号 [{user_data['user']}] 执行时发生异常: {e}\n"
            success = False

        msg += f"🙍🏻‍♂️ 第{i+1}个账号\n{log}\n"

    # === 关键判断：如果所有账号都失败了，则退出程序 ===
    if success_count == 0:
        final_msg = f"❌ 所有 {total_count} 个账号签到均失败，请检查 Cookie 配置！"
        print(final_msg)
        send('夸克自动签到', final_msg)
        sys.exit(0)  # 终止程序
    else:
        summary = f"✅ 签到完成！共 {total_count} 个账号，成功 {success_count} 个，失败 {total_count - success_count} 个。"
        print(summary)

    # 发送完整报告
    try:
        send('夸克自动签到', msg.strip())
    except Exception as err:
        print(f"❌ 发送通知失败: {err}")

    return msg.strip()


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
