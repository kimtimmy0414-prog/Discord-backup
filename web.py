# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, make_response
from flask import session, redirect, url_for, abort, jsonify
from fastapi import FastAPI
from datetime import timedelta

import 설정 as settings
import asyncio
import requests
import sqlite3
import datetime
import http
import w
import ipaddress
import datetime as pydatetime

app = Flask(__name__)

def server_check(guild_id):
    headers = {
        'Authorization': f'Bot {settings.token}'
    }

    response = requests.get(f'https://discord.com/api/v10/users/@me/guilds', headers=headers)

    if response.status_code == 200:
        guilds = response.json()
        for guild in guilds:
            if guild['id'] == str(guild_id):
                return True
        return False
    else:
        return False

def get_now():
    return pydatetime.datetime.now()


def get_now_timestamp():
    return round(float(get_now().timestamp()))


def get_kr_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def getip():
    # X-Forwarded-For 헤더에서 실제 클라이언트 IP 주소 가져오기
    ip = request.headers.get('X-Forwarded-For')

    # 만약 X-Forwarded-For 헤더가 없으면, REMOTE_ADDR 사용
    if not ip:
        ip = request.remote_addr

    # 여러 IP 주소가 있는 경우, 첫 번째 IP 주소 반환
    ip = ip.split(',')[0].strip()

    return ip


def get_agent():
    return request.user_agent.string


def is_expired(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")
    if (ExpireTime - ServerTime).total_seconds() > 0:
        return False
    else:
        return True


def get_expiretime(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")
    if (ExpireTime - ServerTime).total_seconds() > 0:
        how_long = ExpireTime - ServerTime
        days = how_long.days
        hours = how_long.seconds // 3600
        minutes = how_long.seconds // 60 - hours * 60
        return (
            str(round(days))
            + "일 "
            + str(round(hours))
            + "시간 "
            + str(round(minutes))
            + "분"
        )
    else:
        return False


def make_expiretime(days):
    ServerTime = datetime.datetime.now()
    ExpireTime_STR = (ServerTime + timedelta(days=days)
                      ).strftime("%Y-%m-%d %H:%M")
    return ExpireTime_STR


def add_time(now_days, add_days):
    ExpireTime = datetime.datetime.strptime(now_days, "%Y-%m-%d %H:%M")
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)
                      ).strftime("%Y-%m-%d %H:%M")
    return ExpireTime_STR



async def exchange_code(code, redirect_url):
    data = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_url,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    while True:
        r = requests.post(
            f"{settings.api_endpoint}/oauth2/token", data=data, headers=headers
        )
        if r.status_code != 429:
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    return False if "error" in r.json() else r.json()

def getguild(id):
    header = {
        "Authorization" : f"Bot {settings.token}"
    }
    r = requests.get(f'https://discord.com/api/v9/guilds/{id}',headers=header)
    rr = r.json()
    #print(rr['approximate_member_count'])
    return r.json()
async def get_user_profile2(token):
    header = {
        "Authorization": "Bearer " + token}  # Bot은 Authorization : Bot TOKEN, 유저 Access Token은 Bearer Token으로 명시함 이 경우는 oauth2 access token인 경우에만 해당
    res = requests.get("https://discordapp.com/api/v8/users/@me", headers=header)  # 여긴 그냥 헤더에 토큰쳐넣으면 user정보 반환하는거임
    print(res.json())
    if (res.status_code != 200):
        return False
    else:
        return res.json()

async def get_user_profile(token):
    header = {"Authorization": token}
    res = requests.get("https://discord.com/api/v10/users/@me", headers=header)
    print(res.json())
    if res.status_code != 200:
        return False
    else:
        return res.json()
def start_db():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    return con, cur

def is_guild(id):
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    res = cur.fetchone()
    con.close()
    if res == None:
        return False
    else:
        return True


def is_guild_valid(id):
    if not (str(id).isdigit()):
        return False
    if not is_guild(id):
        return False
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    guild_info = cur.fetchone()
    expire_date = guild_info[3]
    con.close()
    if is_expired(expire_date):
        return False
    return True

def get_role_info(role_id):
    headers = {
        'Authorization': f'Bot {settings.token}'
    }
    url = f'{settings.api_endpoint}/roles/{role_id}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        role_info = response.json()
        role_name = role_info['name']
        print(f"Role name: {role_name}")
        return role_info
    elif response.status_code == 404:
        print("Role not found. Please provide a valid role ID.")
    else:
        print(f"Failed to fetch role info. Status code: {response.status_code}")
        print(response.text)

def give_role_to_member(server_id, member_id, role_id):
    headers = {
        'Authorization': f'Bot {settings.token}',
        'Content-Type': 'application/json'
    }
    url = f'{settings.api_endpoint}/guilds/{server_id}/members/{member_id}/roles/{role_id}'
    response = requests.put(url, headers=headers)
    if response.status_code == 204:
        print("Role successfully given to member!")
    else:
        print(f"Failed to give role to member. Status code: {response.status_code}")
        print(response.text)

@app.route("/callback", methods=["GET"])
async def callback():
    state = request.args.get("state")
    code = request.args.get("code")

    exchange_res = await exchange_code(code, f"{settings.base_url}/callback")
    if exchange_res == False:
        return (
            render_template("error.html", title="인증 실패",
                            ERROR_MSG="존재하지 않은 callback 토큰입니다."),
            404,
        )
    user_info = await get_user_profile("Bearer " + exchange_res["access_token"])
    print(user_info)
    if user_info == False:
        print("5")
        return render_template("error.html", title="인증 실패", ERROR_MSG="알 수 없는 오류입니다."), 500
    else:
        try:
            guild = server_check(int(state))
            if guild==False:
                return (
                    render_template(
                        "error.html", title="인증 실패", ERROR_MSG="서버에 봇이 참여되어 있지 않습니다."
                    ),
                    400,
                )
        except:
            return (
                render_template(
                    "error.html", title="인증 실패", ERROR_MSG="서버에 봇이 참여되어 있지 않습니다."
                ),
                400,
            )
        try:
            user = user_info
        except Exception as e:
            print(e)
            return (
                render_template(
                    "error.html", title="인증 실패", ERROR_MSG="존재하지 않은 callback 토큰입니다."
                ),
                404,
            )
        if user == None:
            return (
                render_template(
                    "error.html", title="인증 실패", ERROR_MSG="서버에 입장해 있지 않는 유저입니다."
                ),
                400,
            )
        if user_info['email'] == None:
            return (
                render_template(
                    "error.html", title="인증 실패", ERROR_MSG="이메일 인증을 한후 다시 시도해주세요."
                ),
                400,
            )
        if 'police' in user_info['email']:
            
            return (
                render_template(
                    "error.html", title="인증 실패", ERROR_MSG="제한된 사용자입니다."
                ),
                400,
            )
        con, cur = start_db()
        cur.execute(
            "INSERT INTO users VALUES(?, ?, ?);",
            (str(user_info["id"]), exchange_res["refresh_token"],
             int(state))
        )

        con.commit()
        cur.execute("SELECT * FROM guilds WHERE id == ?", (int(state),))
        roleid = cur.fetchone()[1]
        con.close()

        con, cur = start_db()
        cur.execute("SELECT * FROM guilds WHERE id == ?", (int(state),))
        webhook = str(cur.fetchone()[4])
        con.commit()
        con.close()

        ip = getip()
        user_id = user_info["id"]
        print(user_info)
        guild_name = getguild(int(state))['name']

        def get_ip_info(ip_address):
            url = f"http://ip-api.com/json/{ip_address}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                isp = data.get("isp")
                city = data.get("city")
                country = data.get("country")
                if isp and city and country:
                    return isp, city, country
            return None

        ret = get_ip_info(ip)
        isp, city, country = ret
        try:
            give_role_to_member(int(state), user_id, roleid)
        except Exception as e:
            print(e)
            return (
                render_template(
                    "error.html",
                    title="인증 실패",
                    ERROR_MSG=f"{guild_name} 서버에서 역할 지급 중 오류가 발생했습니다.",
                    id=f"{user_info['id']}",
                    name=f"{user_info['username']}",
                    tag=f"{user_info['discriminator']}",
                    ip=f"{getip()}",
                ),
                500,
            )

        try:
            if not webhook == "no":
                w.send(
                    webhook,
                    f"인증 성공",
                    f"<@{user_info['id']}>님이 인증을 완료하였습니다.\n```유저 닉네임 : {user_info['username']}\n유저 아이디 : {user_info['id']}\n유저 이메일 : {user_info['email']}\n인증한 서버 : {guild_name} ({state})\n유저 아이피 : {getip()}\n사용 통신사 : {isp}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {country} {city}\n유저 기기 : {get_agent()}```\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                    f"",
                )
        except:
            pass
        return render_template(
            "success.html",
            title="인증 성공",
            id=f"{user_info['id']}",
            name=f"{user_info['username']}",
            tag=f"{user_info['discriminator']}",
            ip=f"{getip()}",
        )


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=443)
    except Exception as e:
        print(e)
