import asyncio, requests, sqlite3, datetime, uuid
import disnake as discord
from urllib import parse
from datetime import timedelta
import 설정 as settings
from os import system
from datetime import datetime, timedelta
import requests
from disnake.ext import commands
from disnake import TextInputStyle
import disnake
from discord_webhook import DiscordWebhook, DiscordEmbed
import pytz
import randomstring


intents = discord.Intents.all()

client = commands.Bot(command_prefix="!", intents=intents)
webhoooks = settings.bokweb


def is_expired(time):
    ServerTime = datetime.now()
    ExpireTime = datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        return False
    else:
        return True
def is_admin(user_id):
    if user_id in settings.admin_id:
        return True
    con, cur = start_db()
    cur.execute("CREATE TABLE IF NOT EXISTS admin (user_id INTEGER, expire_date TEXT)")
    cur.execute("SELECT * FROM admin WHERE user_id == ?;", (user_id,))
    user_result = cur.fetchone()
    
    if user_result:
        # 만료일 확인
        expire_date = user_result[1]
        if expire_date and is_expired(expire_date):
            # 만료된 총판 삭제
            cur.execute("DELETE FROM admin WHERE user_id == ?;", (user_id,))
            con.commit()
            con.close()
            return False
        con.close()
        return True
    else:
        con.close()
        return False

def embed(embedtype, embedtitle, description):
    if (embedtype == "error"):
        return discord.Embed(color=0x04e800, title=embedtitle, description=description)
    if (embedtype == "success"):
        return discord.Embed(color=0x04e800, title=embedtitle, description=description)
    if (embedtype == "warning"):
        return discord.Embed(color=0x04e800, title=embedtitle, description=description)
    if (embedtype == "second"):
        return discord.Embed(color=0x04e800, title=embedtitle, description=description)


def get_expiretime(time):
    ServerTime = datetime.now()
    ExpireTime = datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        how_long = (ExpireTime - ServerTime)
        days = how_long.days
        hours = how_long.seconds // 3600
        minutes = how_long.seconds // 60 - hours * 60
        return str(round(days)) + "일 " + str(round(hours)) + "시간 " + str(round(minutes)) + "분"
    else:
        return False


def make_expiretime(days):
    ServerTime = datetime.now()
    ExpireTime_STR = (ServerTime + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR


def add_time(now_days, add_days):
    ExpireTime = datetime.strptime(now_days, '%Y-%m-%d %H:%M')
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR


async def exchange_code(code, redirect_url):
    data = {
        'client_id': settings.client_id,
        'client_secret': settings.client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_url
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % settings.api_endpoint, data=data, headers=headers)
        if (r.status_code != 429):
            break
        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    return False if "error" in r.json() else r.json()


async def refresh_token(refresh_token):
    data = {
        'client_id': settings.client_id,
        'client_secret': settings.client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % settings.api_endpoint, data=data, headers=headers)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)

    return False if "error" in r.json() else r.json()


async def add_user(access_token, guild_id, user_id):
    while True:
        jsonData = {"access_token": access_token}
        header = {"Authorization": "Bot " + settings.token}
        r = requests.put(f"{settings.api_endpoint}/guilds/{guild_id}/members/{user_id}", json=jsonData, headers=header)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)

    if (r.status_code == 201 or r.status_code == 204):
        return {'result':True}
    else:
        print(r.json())
        return {"result":False,'reason':r.json()['message']}


async def get_user_profile(token):
    header = {"Authorization": token}
    res = requests.get("https://discordapp.com/api/v8/users/@me", headers=header)
    print(res.json())
    if (res.status_code != 200):
        return False
    else:
        return res.json()


def start_db():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    return con, cur


async def is_guild(id):
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    res = cur.fetchone()
    con.close()
    if (res == None):
        return False
    else:
        return True


def eb(embedtype, embedtitle, description):
    if (embedtype == "error"):
        return discord.Embed(color=0x04e800, title=":no_entry: " + embedtitle, description=description)
    if (embedtype == "success"):
        return discord.Embed(color=0x04e800, title=":white_check_mark: " + embedtitle, description=description)
    if (embedtype == "warning"):
        return discord.Embed(color=0x04e800, title=":warning: " + embedtitle, description=description)
    if (embedtype == "loading"):
        return discord.Embed(color=0x04e800, title=":gear: " + embedtitle, description=description)
    if (embedtype == "primary"):
        return discord.Embed(color=0x04e800, title=embedtitle, description=description)


async def is_guild_valid(id):
    if not (str(id).isdigit()):
        return False
    if not (await is_guild(id)):
        return False
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    guild_info = cur.fetchone()
    expire_date = guild_info[3]
    con.close()
    if (is_expired(expire_date)):
        return False
    return True


owner = settings.admin_id
global imjoin
imjoin=0
@client.event
async def on_guild_join(guild):
    global imjoin
    imjoin = guild

    print(f'Joined new guild: {guild.name}')

# @client.slash_command(name="복구", description="서버 인원을 복구합니다.")
# @commands.has_permissions(administrator=True)
# @commands.guild_only()
# async def restore(
#         inter: discord.ApplicationCommandInteraction,
#         라이센스: str
# ):
#     if (inter.user.id) in owner or inter.user.guild_permissions.administrator:
#         recover_key = 라이센스
#         con, cur = start_db()
#         cur.execute("SELECT * FROM guilds WHERE token == ?;", (recover_key,))
#         token_result = cur.fetchone()
#         con.close()
#         if (token_result == None):
#             await inter.response.send_message(embed=embed("error", "오류", "존재하지 않는 복구 키입니다. 관리자에게 문의해주세요,"))
#             return
#         if not (await is_guild_valid(token_result[0])):
#             await inter.response.send_message(embed=embed("error", "오류", "만료된 복구 키입니다. 관리자에게 문의해주세요."))
#             return
#         if not (await inter.guild.fetch_member(client.user.id)).guild_permissions.administrator:
#             await inter.response.send_message(embed=embed("error", "오류", "복구를 위해서는 봇이 관리자 권한을 가지고 있어야 합니다."))
#             return

#         con, cur = start_db()
#         cur.execute("SELECT * FROM users WHERE guild_id == ?;", (token_result[0],))
#         users = cur.fetchall()
#         con.close()

#         users = list(set(users))

#         await inter.response.send_message(embed=embed("success", "성공", "유저 복구 중입니다. 최대 2시간이 소요될 수 있습니다."))

#         for user in users:
#             try:
#                 refresh_token1 = user[1]
#                 user_id = user[0]
#                 new_token = await refresh_token(refresh_token1)
#                 if (new_token != False):
#                     new_refresh = new_token["refresh_token"]
#                     new_token = new_token["access_token"]
#                     await add_user(new_token, inter.guild.id, user_id)
#                     print(new_token)
#                     con, cur = start_db()
#                     cur.execute("UPDATE users SET token = ? WHERE token == ?;", (new_refresh, refresh_token1))
#                     con.commit()
#                     con.close()
#             except:
#                 pass
#         await inter.channel.send(embed=embed("success", "성공", "유저 복구가 완료되었습니다."))


class GetId(disnake.ui.Modal):

    def __init__(self, bot):
        components = [
            disnake.ui.TextInput(
                label="서버 ID를 입력해주세요.",
                placeholder=f"ex) 1158698657701449738",
                custom_id="gid",
                style=disnake.TextInputStyle.short,
                min_length=18,
                max_length=19,
            ),
        ]
        super().__init__(
            title=f"추가한 서버의 ID입력",
            custom_id="charge_modal",
            components=components,
        )
        self.client = client


class Key(disnake.ui.Modal):

    def __init__(self, bot):
        components = [
            disnake.ui.TextInput(
                label="복구키를 입력해주세요.",
                custom_id="key",
                style=disnake.TextInputStyle.short,
            ),
        ]
        super().__init__(
            title=f"사용할 복구키 입력",
            custom_id="charge_modal",
            components=components,
        )
        self.client = client


@client.listen("on_button_click")
async def help_listener(inter: discord.MessageInteraction):
    global imjoin
    def embed(embedtype, embedtitle, description):
        if (embedtype == "error"):
            return discord.Embed(color=0x04e800, title=embedtitle, description=description)
        if (embedtype == "success"):
            return discord.Embed(color=0x04e800, title=embedtitle, description=description)
        if (embedtype == "warning"):
            return discord.Embed(color=0x04e800, title=embedtitle, description=description)
        if (embedtype == "second"):
            return discord.Embed(color=0x04e800, title=embedtitle, description=description)

    tok = inter.component.custom_id
    if (tok.startswith("loginfo")):
        if inter.author.guild_permissions.administrator:
            log_id=tok.split("_")[1]
            con, cur = start_db()
            cur.execute("SELECT * FROM log_ids WHERE log_id == ?;", (log_id,))
            log_result = cur.fetchone()
            con.close()
            await inter.response.send_message(embed=embed("success", "해당 복구 기록입니다.", log_result[1]),
                                              ephemeral=True)
        else:
            await inter.response.send_message(embed=embed("error", "관리자만 사용가능합니다.", ""),
                                              ephemeral=True)
    if (tok.startswith("start")):
        await inter.response.send_modal(modal=Key(inter.client))
        try:

            modal_inter: disnake.ModalInteraction = await client.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "charge_modal" and i.author.id == inter.author.id,
                timeout=None,
            )
        except asyncio.TimeoutError:
            return
        recover_key = modal_inter.text_values['key']
        con, cur = start_db()
        cur.execute("SELECT * FROM code WHERE code == ?;", (recover_key,))
        token_result = cur.fetchone()
        con.close()
        if (token_result == None):
            await modal_inter.response.send_message(embed=embed("error", "오류", "존재하지 않는 복구 키입니다. 관리자에게 문의해주세요,"),
                                                    ephemeral=True)
            return
        if not (await modal_inter.guild.fetch_member(client.user.id)).guild_permissions.administrator:
            await inter.response.send_message(embed=embed("error", "오류", "복구를 위해서는 봇이 관리자 권한을 가지고 있어야 합니다."),
                                              ephemeral=True)
            return
        await modal_inter.response.send_message(
            embed=discord.Embed(title="🚀 아래 파란글씨를 눌러 봇을 서버에 추가해주세요.",
                                description=f"**[봇초대링크](https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot)를 눌러 서버에 추가후\n아래 버튼을 눌러서 추가한 서버의 ID를 입력해주세요**",
                                color=0x04e800),
            components=[
                [
                    discord.ui.Button(label=f"✅ 추가 완료", style=discord.ButtonStyle.green,
                                      custom_id=f'gogo_{recover_key}'),
                    discord.ui.Button(style=discord.ButtonStyle.link, label="봇 초대하기",
                               url=f'https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot')
                ]], ephemeral=True)

    if (tok.startswith("gogo")):
        if imjoin!=0:
            embed=discord.Embed(title="서버 자동 추천",
                                description=f"**`{imjoin.name}` 가 본인서버가 맞나요?\n\n아니라면 `아니요`를 눌러 서버아이디를 직접 입력해주세요.**",
                                color=0x04e800)
            try:
                embed.set_thumbnail(url=imjoin.icon.url)
            except:
                pass
            await inter.send(embed=embed,
            components=[
                [
                    discord.ui.Button(label=f"네, 맞습니다.", style=discord.ButtonStyle.green, custom_id=f'yes'),
                    discord.ui.Button(label=f"아니요", style=discord.ButtonStyle.red, custom_id=f'no'),
                ]],ephemeral=True)
            try:
                inter: disnake.Interaction = await client.wait_for("button_click", check=lambda
                    i: i.
                    component.custom_id in ["yes", "no"] and i.author.id == inter.author.id,
                                                              timeout=None)
            except:
                return
            if inter.component.custom_id == "yes":
                guild_id=imjoin.id
                modal_inter=inter
                await modal_inter.response.defer(ephemeral=True)
                pass
            else:
                await inter.response.send_modal(modal=GetId(inter.client))
                try:

                    modal_inter: disnake.ModalInteraction = await client.wait_for(
                        "modal_submit",
                        check=lambda i: i.custom_id == "charge_modal" and i.author.id == inter.author.id,
                        timeout=None,
                    )
                except asyncio.TimeoutError:
                    return
                guild_id = modal_inter.text_values['gid']
                await modal_inter.response.defer(ephemeral=True)
        else:
            await inter.response.send_modal(modal=GetId(inter.client))
            try:

                modal_inter: disnake.ModalInteraction = await client.wait_for(
                    "modal_submit",
                    check=lambda i: i.custom_id == "charge_modal" and i.author.id == inter.author.id,
                    timeout=None,
                )
            except asyncio.TimeoutError:
                return
            guild_id = modal_inter.text_values['gid']
            await modal_inter.response.defer(ephemeral=True)

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

        value = (server_check(guild_id))
        if value == True:
            recover_key = tok[5:]
            con, cur = start_db()
            cur.execute("SELECT * FROM code WHERE code == ?;", (recover_key,))
            token_result = cur.fetchone()
            con.close()

            until = token_result[1]

            con, cur = start_db()
            cur.execute("DELETE FROM code WHERE code = ?", (recover_key,))
            con.commit()
            con.close()

            real_try = until * 3.612
            hundreds_place_value = int(real_try // 100)

            predict_time = hundreds_place_value * 2

            # Converting minutes to hours and minutes if over 60 minutes
            hours = predict_time // 60
            minutes = predict_time % 60

            if hours > 0:
                result = f"{hours}시간 {minutes}분"
            else:
                result = f"{minutes}분"
            con, cur = start_db()
            cur.execute("SELECT * FROM restore_log")
            restore_log = cur.fetchall()
            con.close()

            channel_ids = [id for id in webhoooks]
            for log in restore_log:
                channel_id = log[0]
                admin_id = log[1]
                if is_admin(admin_id):
                    channel_ids.append(channel_id)

            channel_ids = list(set(channel_ids))


            for channel_id in channel_ids:
                try:
                    embeds = disnake.Embed(
                        title="복구봇 사용 중", description=f"{inter.user.name}님의 {until}명 복구를 시작합니다.\n―――――――――――――――――――\n예상 복구 시간은 **__{result}__** 입니다.", color=0x04e800
                    )
                    embeds.timestamp = datetime.now()
                    channel = client.get_channel(channel_id)
                    await channel.send(embed=embeds)
                except:
                    pass

            embedt = discord.Embed(
                title="성공",
                description=f"{until}명의 유저를 복구 중입니다. 예상 시간 {result}입니다. (예상 복구 인원: {until})",
                color=0x04e800
            )
            g = client.get_guild(int(guild_id))
            previous = len(g.members)
            print(previous)
            use_list = []
            await modal_inter.edit_original_response(embed=embedt,components=[])

            con, cur = start_db()
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()
            con.close()

            users = list(set(users))
            success = 0
            fail = 0
            k=0
            message_count={}
            duplicate_list = []

            while True:
                try:
                    refresh_token1 = users[k][1]
                    user_id = users[k][0]
                    
                    member = g.get_member(user_id)
                    if member:
                        use_list.append(user_id)
                        duplicate_list.append(user_id)
                        
                    if not user_id in use_list:
                        use_list.append(user_id)
                        new_token = await refresh_token(refresh_token1)
                        if (new_token != False):
                            new_refresh = new_token["refresh_token"]
                            new_token = new_token["access_token"]
                            ss = await add_user(new_token, int(guild_id), user_id)

                            con, cur = start_db()
                            cur.execute("UPDATE users SET token = ? WHERE token == ?;",
                                        (new_refresh, refresh_token1))
                            con.commit()
                            con.close()
                            
                            if ss['result'] == True:
                                success += 1
                                if success==until:
                                    break
                            else:
                                fail += 1
                                message = ss.get('reason')
                                if message:
                                    if message in message_count:
                                        message_count[message] += 1
                                    else:
                                        message_count[message] = 1

                            

                        else:
                            fail += 1
                            con, cur = start_db()
                            cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
                            con.commit()
                            con.close()
                    k+=1
                    if k == len(users):
                        break

                except:
                    pass
            embedt = discord.Embed(
                title="성공",
                description=f"유저 복구가 완료되었습니다.\n봇을 추방하여 주세요.",
                color=0x04e800
            )
            try:
                await inter.user.send(embed=embedt)
            except:
                pass
            g = client.get_guild(int(guild_id))
            now = len(g.members)
            print(now)
            print(previous)

            log_id = randomstring.pick(6)
            con, cur = start_db()
            cur.execute("INSERT INTO log_ids VALUES(?, ?);", (log_id, f"서버 이름 : {g.name}\n서버 아이디 : {g.id}\n복구 전 서버 인원 : {previous}\n\n{message_count}"))
            con.commit()
            con.close()

            for channel_id in channel_ids:
                try:
                    embeds = disnake.Embed(
        title="복구봇 사용 완료",
        description=f'''
    `{inter.user.name}`님의 `{until}`명 복구가 완료되었습니다.

    - 결과\n - 총 시도 횟수 : `{success + fail}`
    - 성공 : `{success}`
    - 실패 `{fail}`
    - 중복 추가된 인원 : `{len(duplicate_list)}`

    ''',
        color=0x04e800)
                    # - 서버참가후 나간 인원 : `{(now - previous) - success}` <:warn_user:1184504362991620156>
                    embeds.timestamp = datetime.now()
                    channel = client.get_channel(channel_id)
                    await channel.send(embed=embeds,components=[
                        discord.ui.Button(label="상세 정보", style=discord.ButtonStyle.green, custom_id=f"loginfo_{log_id}"),
                    ])
                except:
                    pass
        else:
            embed = disnake.Embed(title='서버 확인실패', description=f"알 수 없는 오류가 발생했습니다.", color=0x04e800)
            await modal_inter.edit_original_response(embed=embed)
    if (tok.startswith("인원새로고침")):
        if is_admin(inter.user.id):
            seoul_timezone = pytz.timezone('Asia/Seoul')

            current_time = datetime.now(seoul_timezone)
            timestamp = int(current_time.timestamp())
            await inter.response.send_message(embed=embed("success", "새로고침 중", "인원 새로고침을 시작합니다."), ephemeral=True)
            await inter.message.edit(content="",
                                     embed=embed("warning", "인원 새로고침 중", f"인원 새로고침 중입니다. \n\n기준 시각: <t:{timestamp}:f>"),
                                     components=[discord.ui.Button(label="인원 새로고침", style=discord.ButtonStyle.secondary,
                                                                   disabled=True, custom_id=f"인원새로고침"),
                                                 discord.ui.Button(label="버튼 리셋", style=discord.ButtonStyle.danger,
                                                                   custom_id=f"강제종료")])
            con, cur = start_db()
            cur.execute("SELECT * FROM restore_log")
            restore_log = cur.fetchall()
            con.close()
            channel_ids = [id for id in webhoooks]
            for log in restore_log:
                channel_id = log[0]
                admin_id = log[1]
                if is_admin(admin_id):
                    channel_ids.append(channel_id)
            channel_ids = list(set(channel_ids))
            for channel_id in channel_ids:
                try:
                    embeds = disnake.Embed(
                        title="인원 새로고침 중", description=f"인원을 체킹하는중입니다.", color=0x04e800
                    )
                    embeds.timestamp = datetime.now()
                    channel = client.get_channel(channel_id)
                    await channel.send(embed=embeds)
                except:
                    pass
            inw = 0
            con, cur = start_db()
            cur.execute("SELECT * FROM users")
            us_result = cur.fetchall()
            con.close()
            users = list(set(us_result))
            for user in users:
                try:
                    refresh_token1 = user[1]
                    new_token = await refresh_token(refresh_token1)
                    if (new_token != False):
                        new_refresh = new_token["refresh_token"]
                        new_token = new_token["access_token"]
                        inw += 1
                        print(inw)
                        con, cur = start_db()
                        cur.execute("UPDATE users SET token = ? WHERE token == ?;", (new_refresh, refresh_token1))
                        con.commit()
                        con.close()
                    else:
                        con, cur = start_db()
                        cur.execute("DELETE FROM users WHERE token == ?;", (refresh_token1,))
                        con.commit()
                        con.close()

                except:
                    pass

            con, cur = start_db()
            cur.execute("SELECT * FROM users")
            us_result = cur.fetchall()
            con.close()

            user_list = []

            for i in range(len(us_result)):
                user_list.append(us_result[i][0])

            new_list = []

            for v in user_list:
                if v not in new_list:
                    new_list.append(v)
                else:
                    con, cur = start_db()
                    cur.execute(
                        "DELETE FROM users WHERE id == ? AND ROWID IN (SELECT ROWID FROM users WHERE id == ? LIMIT 1);",
                        (v, v))
                    con.commit()
                    con.close()
                    pass
            
            for channel_id in channel_ids:
                try:
                    embeds = disnake.Embed(
                        title="인원 새로고침완료",
                        description=f'''
    - 결과\n - 예상 복구 인원 : `{len(new_list)}` 

    ''', color=0x04e800
                    )
                    embeds.timestamp = datetime.now()
                    channel = client.get_channel(channel_id)
                    await channel.send(embed=embeds)
                except:
                    pass

            await inter.message.edit(embed=embed("second", "인원 새로고침",
                                                 f"인원 새로고침을 하려면 아래 버튼을 눌러주세요.\n\n**> 예상복구인원 `{len(new_list)}` 명 입니다.**\n\n기준 시각: <t:{timestamp}:f>"),
                                     components=[discord.ui.Button(label="인원 새로고침", style=discord.ButtonStyle.secondary,
                                                                   custom_id=f"인원새로고침", disabled=False)])


@client.event
async def on_message(message):

    if message.author.bot:
        return
    if is_admin(message.author.id):
        if (message.content.startswith("!인원메시지생성")):
            await message.delete()
            await message.channel.send(embed=embed("second", "인원 새로고침", "인원 새로고침을 하려면 아래 버튼을 눌러주세요."), components=[
                discord.ui.Button(label="인원 새로고침", style=discord.ButtonStyle.secondary, custom_id=f"인원새로고침")])


@client.slash_command(name="자동화", description="복구키 사용 임베드 출력")
@commands.guild_only()
async def restoreeb(
        inter: discord.ApplicationCommandInteraction,
):
    await inter.response.send_message(
        embed=discord.Embed(title="복구키 사용하기",
                            description='복구키를 사용하려면 아래 버튼을 클릭해주세요.',
                            color=0x04e800),
        components=[
            [
                discord.ui.Button(label=f"복구봇 사용하기", style=discord.ButtonStyle.grey, custom_id=f'start')
            ]])


# @client.slash_command(name="복구키사용", description="복구키를 이용해 인원을 복구합니다.")
# @commands.guild_only()
# async def restore(
#         inter: discord.ApplicationCommandInteraction,
#         복구키: str
# ):
#     recover_key = 복구키
#     con, cur = start_db()
#     cur.execute("SELECT * FROM code WHERE code == ?;", (recover_key,))
#     token_result = cur.fetchone()
#     con.close()
#     if (token_result == None):
#         await inter.response.send_message(embed=embed("error", "오류", "존재하지 않는 복구 키입니다. 관리자에게 문의해주세요,"), ephemeral=True)
#         return
#     if not (await inter.guild.fetch_member(client.user.id)).guild_permissions.administrator:
#         await inter.response.send_message(embed=embed("error", "오류", "복구를 위해서는 봇이 관리자 권한을 가지고 있어야 합니다."),
#                                           ephemeral=True)
#         return
#     await inter.response.send_message(
#         embed=discord.Embed(title="🚀 아래 파란글씨를 눌러 봇을 서버에 추가해주세요.",
#                             description=f"**[봇초대링크](https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot)를 눌러 서버에 추가후\n아래 버튼을 눌러서 추가한 서버의 ID를 입력해주세요**",
#                             color=0xff9114),
#         components=[
#             [
#                 discord.ui.Button(label=f"✅ 추가 완료", style=discord.ButtonStyle.green, custom_id=f'gogo_{복구키}')
#             ]], ephemeral=True)


@client.slash_command(name="복구키생성", description="복구키를 생성합니다.")
@commands.has_permissions(administrator=True)
async def createrestket(
        inter: discord.ApplicationCommandInteraction,
        개수: int,
        인원: int
):
    if not is_admin(inter.user.id):
        await inter.response.send_message(embed=embed("error", "오류", "해당 명령어를 사용할 권한이 없습니다."), ephemeral=True)
        return

    amount = 인원
    long = 개수
    if (long >= 1 and long <= 1000):
        con, cur = start_db()
        generated_key = []
        for _ in range(long):
            key = str(uuid.uuid4())
            generated_key.append(key)
            cur.execute("INSERT INTO code VALUES(?, ?);", (key, amount))
        con.commit()
        con.close()
        generated_key = "\n".join(generated_key)

        try:
            await inter.response.send_message(generated_key,
                                              embed=embed("success", f"{amount}명 복구키 {long}개 생성 성공", generated_key))
        except:
            file_name = 'lic.txt'
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(generated_key)
            with open(file_name, 'rb') as file:
                file_data = discord.File(file, filename='lic.txt')
                await inter.response.send_message(
                    embed=embed("success", f"{amount}명 복구키 {long}개 생성 성공", "생성이 완료되었습니다."), file=file_data)

    else:
        await inter.response.send_message(embed=embed("error", "오류", "최대 1,000개까지 생성 가능합니다."), ephemeral=True)


@client.slash_command(name="생성", description="복구봇 라이센스를 생성합니다.")
@commands.has_permissions(administrator=True)
async def createbotkey(
        inter: discord.ApplicationCommandInteraction,
        일수: int,
        개수: int
):
    if not is_admin(inter.user.id):
        await inter.response.send_message(embed=embed("error", "오류", "해당 명령어를 사용할 권한이 없습니다."), ephemeral=True)
        return

    amount = 일수
    long = 개수
    if (long >= 1 and long <= 1000):
        con, cur = start_db()
        generated_key = []
        for _ in range(long):
            key = str(uuid.uuid4())
            generated_key.append(key)
            cur.execute("INSERT INTO licenses VALUES(?, ?);", (key, amount))
        con.commit()
        con.close()
        generated_key = "\n".join(generated_key)

        try:
            await inter.response.send_message(generated_key, embed=embed("success", f"{amount}일 복구봇 라이센스 {long}개 생성 성공",
                                                                         generated_key))
        except:
            file_name = 'lic.txt'
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(generated_key)
            with open(file_name, 'rb') as file:
                file_data = discord.File(file, filename='lic.txt')
                await inter.response.send_message(
                    embed=embed("success", f"{amount}일 복구봇 라이센스 {long}개 생성 성공", "생성이 완료되었습니다."), file=file_data)

    else:
        await inter.response.send_message(embed=embed("error", "오류", "최대 1,000개까지 생성 가능합니다."), ephemeral=True)


@client.slash_command(name="역할", description="역할을 설정합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def roleset(
        inter: discord.ApplicationCommandInteraction,
        역할: discord.Role):
    if not (await is_guild_valid(inter.guild.id)):
        await inter.response.send_message(embed=embed("error", "오류", "유효한 라이센스가 존재하지 않습니다."), ephemeral=True)
        return
    if (await is_guild_valid(inter.guild.id)):
        role_info = 역할
        if (role_info == None):
            await inter.response.send_message(embed=embed("error", "오류", "존재하지 않는 역할입니다."), ephemeral=True)
            return

        con, cur = start_db()
        cur.execute("UPDATE guilds SET role_id = ? WHERE id == ?;", (role_info.id, inter.guild.id))
        con.commit()
        con.close()
        await inter.response.send_message(embed=embed("success", "역할 설정 성공", "인증을 완료한 유저에게 해당 역할이 지급됩니다."))


@client.slash_command(name="로그웹훅", description="웹훅을 설정합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def webhookset(
        inter: discord.ApplicationCommandInteraction,
        웹훅: str):
    if not (await is_guild_valid(inter.guild.id)):
        await inter.response.send_message(embed=embed("error", "오류", "유효한 라이센스가 존재하지 않습니다."), ephemeral=True)
        return
    webhook = 웹훅
    con, cur = start_db()
    cur.execute("UPDATE guilds SET verify_webhook == ? WHERE id = ?;", (str(webhook), inter.guild.id))
    con.commit()
    con.close()
    await inter.response.send_message(embed=embed("success", "인증로그 웹훅저장 성공", f"인증을 완료한후 {webhook} 으로 인증로그가 전송됩니다"))


@client.slash_command(name="인증", description="인증 메시지를 전송합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def verify(
        inter: discord.ApplicationCommandInteraction):
    if not (await is_guild_valid(inter.guild.id)):
        await inter.response.send_message(embed=embed("error", "오류", "유효한 라이센스가 존재하지 않습니다."), ephemeral=True)
        return
    rd_url = f'https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}%2Fcallback&response_type=code&scope=identify%20guilds.join%20email&state={inter.guild.id}'
    view = discord.ui.View()
    button = discord.ui.Button(style=discord.ButtonStyle.link, label="🌐 인증하러가기",
                               url=rd_url)
    view.add_item(button)
    await inter.response.send_message(embed=embed("success", "인증 메시지 전송", f"인증 메시지가 전송되었습니다."), ephemeral=True)
    await inter.channel.send(embed=discord.Embed(color=0x04e800, title="Backup service",
                                                 description=f"Please authorize your account [here]({rd_url}) to see other channels.\n다른 채널을 보려면 [여기]({rd_url}) 를 눌러 계정을 인증해주세요."),
                             view=view)


@client.slash_command(name="총판라이센스생성", description="총판라이센스를 생성합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def create_admin_license(
        inter: discord.ApplicationCommandInteraction,
        일수: int,
        개수: int
):
    if inter.user.id not in owner:
        await inter.response.send_message(embed=embed("error", "오류", "해당 명령어를 사용할 권한이 없습니다."), ephemeral=True)
        return
    amount = 일수
    long = 개수
    if (long >= 1 and long <= 1000):
        con, cur = start_db()
        generated_key = []
        for _ in range(long):
            key = str(uuid.uuid4())
            generated_key.append(key)
            cur.execute("CREATE TABLE IF NOT EXISTS admin_licenses (key TEXT, days INTEGER)")   
            cur.execute("INSERT INTO admin_licenses VALUES(?, ?);", (key, amount))
        con.commit()
        con.close()
        generated_key = "\n".join(generated_key)
        try:
            await inter.response.send_message(generated_key, embed=embed("success", f"{amount}일 총판라이센스 {long}개 생성 성공",
                                                                         generated_key))
        except:
            file_name = 'lic.txt'
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(generated_key)   

@client.slash_command(name="총판라센등록", description="총판라이센스를 등록합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def register_admin_license(
        inter: discord.ApplicationCommandInteraction,
        라이센스: str):
        
    con, cur = start_db()
    cur.execute("SELECT * FROM admin_licenses WHERE key == ?;", (라이센스,))
    key_info = cur.fetchone()
    if (key_info == None):
        await inter.response.send_message(embed=embed("error", "오류", "존재하지 않거나 이미 사용된 라이센스입니다."), ephemeral=True)
        return
    
    # 라이센스 삭제
    cur.execute("DELETE FROM admin_licenses WHERE key == ?;", (라이센스,))
    con.commit()
    
    # 총판 테이블 구조 변경 (만료일 추가)
    cur.execute("CREATE TABLE IF NOT EXISTS admin (user_id INTEGER, expire_date TEXT)")
    
    # 현재 날짜에 라이센스 기간을 더한 만료일 계산
    expire_date = make_expiretime(key_info[1])
    
    # 기존 총판인지 확인
    cur.execute("SELECT * FROM admin WHERE user_id == ?;", (inter.user.id,))
    existing_admin = cur.fetchone()
    
    if existing_admin:
        # 기존 총판인 경우 만료일 업데이트
        cur.execute("UPDATE admin SET expire_date = ? WHERE user_id == ?;", (expire_date, inter.user.id))
    else:
        # 새로운 총판인 경우 추가
        cur.execute("INSERT INTO admin VALUES(?, ?);", (inter.user.id, expire_date))
    
    con.commit()
    con.close()
    await inter.response.send_message(embed=embed("success", "총판라이센스 등록 성공", f"총판라이센스가 등록되었습니다. 만료일: {expire_date}"))


@client.slash_command(name="총판추가", description="총판을 추가합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def add_admin(
        inter: discord.ApplicationCommandInteraction,
        총판: discord.Member,
        일수: int):
    if inter.user.id in owner:
        con, cur = start_db()
        cur.execute("CREATE TABLE IF NOT EXISTS admin (user_id INTEGER, expire_date TEXT)")
        
        # 현재 날짜에 지정된 일수를 더한 만료일 계산
        expire_date = make_expiretime(일수)
        
        # 기존 총판인지 확인
        cur.execute("SELECT * FROM admin WHERE user_id == ?;", (총판.id,))
        existing_admin = cur.fetchone()
        
        if existing_admin:
            # 기존 총판인 경우 만료일 업데이트
            cur.execute("UPDATE admin SET expire_date = ? WHERE user_id == ?;", (expire_date, 총판.id))
        else:
            # 새로운 총판인 경우 추가
            cur.execute("INSERT INTO admin VALUES(?, ?);", (총판.id, expire_date))
        
        con.commit()
        con.close()
        await inter.response.send_message(embed=embed("success", "총판 추가 성공", f"총판이 추가되었습니다. 만료일: {expire_date}"))


@client.slash_command(name="복구로그설정", description="복구로그를 설정합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def add_restore_log(
        inter: discord.ApplicationCommandInteraction,
        채널: discord.TextChannel):
    if is_admin(inter.user.id):
        con, cur = start_db()
        cur.execute("CREATE TABLE IF NOT EXISTS restore_log (channel_id INTEGER, admin_id INTEGER)")
        cur.execute("INSERT INTO restore_log VALUES(?, ?);", (채널.id, inter.user.id))
        con.commit()
        con.close()
        await inter.response.send_message(embed=embed("success", "복구로그 설정 성공", "복구로그가 설정되었습니다."))
    else:
        await inter.response.send_message(embed=embed("error", "오류", "해당 명령어를 사용할 권한이 없습니다."), ephemeral=True)
        return

@client.slash_command(name="총판삭제", description="총판을 삭제합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def delete_admin(
        inter: discord.ApplicationCommandInteraction,
        총판: discord.Member):
    
    if inter.user.id in owner:
        con, cur = start_db()
        cur.execute("CREATE TABLE IF NOT EXISTS admin (user_id INTEGER, expire_date TEXT)")
        cur.execute("DELETE FROM admin WHERE user_id == ?;", (총판.id,))
        con.commit()
        con.close()
        await inter.response.send_message(embed=embed("success", "총판 삭제 성공", "총판이 삭제되었습니다."))


@client.slash_command(name="웹훅보기", description="설정된 웹훅을 확인합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def vwebhook(
        inter: discord.ApplicationCommandInteraction):
    if not (await is_guild_valid(inter.guild.id)):
        await inter.response.send_message(embed=embed("error", "오류", "유효한 라이센스가 존재하지 않습니다."), ephemeral=True)
        return
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (inter.guild.id,))
    guild_info = cur.fetchone()
    con.close()
    if guild_info[4] == "":
        await inter.response.send_message(embed=embed("error", "오류", "웹훅이 없습니다."), ephemeral=True)
        return
    await inter.response.send_message(f"{guild_info[4]}")
@client.slash_command(name='서버정리', description=f'관리자 전용 명령어')
async def 서버정리(ctx):
    if ctx.user.id in owner:
        await ctx.response.defer()

        nolicense = []

        async for guild in client.fetch_guilds():
            server = guild.id

            if not (await is_guild(server)):
                await guild.leave()
                nolicense.append(f'{guild.name}({guild.id})')
        nolicenseStr = '\n'.join(nolicense)
        await ctx.edit_original_message(f"""```
서버가 정리되었습니다

TOTAL {len(nolicense)}

라이센스 미등록 {len(nolicense)}

라이센스 미등록 서버
{nolicenseStr}
```""")

@client.slash_command(name="정보", description="라이센스 정보를 확인합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def vinfo(
        inter: discord.ApplicationCommandInteraction):
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (inter.guild.id,))
    guild_info = cur.fetchone()
    con.close()
    await inter.response.send_message(
        embed=embed("success", "라이센스 정보", f"{get_expiretime(guild_info[3])} 남음\n{guild_info[3]} 까지 이용이 가능합니다"))


@client.slash_command(name="등록", description="라이센스를 등록합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def webhookset(
        inter: discord.ApplicationCommandInteraction,
        라이센스: str):
    license_number = 라이센스
    con, cur = start_db()
    cur.execute("SELECT * FROM licenses WHERE key == ?;", (license_number,))
    key_info = cur.fetchone()
    if (key_info == None):
        con.close()
        await inter.response.send_message(embed=embed("error", "오류", "존재하지 않거나 이미 사용된 라이센스입니다."), ephemeral=True)
        return
    cur.execute("DELETE FROM licenses WHERE key == ?;", (license_number,))
    con.commit()
    con.close()
    key_length = key_info[1]

    if (await is_guild(inter.guild.id)):
        con, cur = start_db()
        cur.execute("SELECT * FROM guilds WHERE id == ?;", (inter.guild.id,))
        guild_info = cur.fetchone()
        expire_date = guild_info[3]
        if (is_expired(expire_date)):
            new_expiredate = make_expiretime(key_length)
        else:
            new_expiredate = add_time(expire_date, key_length)

        cur.execute("UPDATE guilds SET expiredate = ? WHERE id == ?;", (new_expiredate, inter.guild.id))
        con.commit()
        con.close()
        await inter.response.send_message(embed=embed("success", "성공", f"{key_length} 일 라이센스가 성공적으로 등록되었습니다."))

    else:
        con, cur = start_db()
        new_expiredate = make_expiretime(key_length)
        recover_key = str(uuid.uuid4())[:8].upper()
        cur.execute("INSERT INTO guilds VALUES(?, ?, ?, ?, ?);", (inter.guild.id, 0, recover_key, new_expiredate, "no"))
        con.commit()
        con.close()
        await inter.response.send_message(f"{inter.user.mention} 님 디엠을 확인해주세요")
        await inter.user.send(
            embed=embed("success", "Backup service", f"복구 키 : `{recover_key}`\n해당 키를 꼭 기억하거나 저장해 주세요."))


@client.event
async def on_ready():
    print(
        f"Login: {client.user}\nInvite Link: https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot")
    
    # 만료된 총판 정리 태스크 시작
    client.loop.create_task(cleanup_expired_admins())
    
    while True:
        await client.change_presence(activity=discord.Game(name=str(len(client.guilds)) + "개의 서버이용"))
        await asyncio.sleep(5)
        await client.change_presence(
            activity=discord.Activity(name=str(len(client.guilds)) + "개의 서버이용", type=discord.ActivityType.watching))
        await asyncio.sleep(5)


async def cleanup_expired_admins():
    """만료된 총판을 자동으로 정리하는 함수"""
    while True:
        try:
            con, cur = start_db()
            cur.execute("CREATE TABLE IF NOT EXISTS admin (user_id INTEGER, expire_date TEXT)")
            cur.execute("SELECT * FROM admin")
            admins = cur.fetchall()
            
            for admin in admins:
                user_id = admin[0]
                expire_date = admin[1]
                
                if expire_date and is_expired(expire_date):
                    # 만료된 총판 삭제
                    cur.execute("DELETE FROM admin WHERE user_id == ?;", (user_id,))
                    print(f"만료된 총판 삭제: {user_id}")
            
            con.commit()
            con.close()
            
            # 1시간마다 체크
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"총판 정리 중 오류 발생: {e}")
            await asyncio.sleep(3600)


@client.slash_command(name="총판정보", description="총판 정보를 확인합니다.")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def admin_info(
        inter: discord.ApplicationCommandInteraction,
        총판: discord.Member):
    
    if inter.user.id in owner:
        con, cur = start_db()
        cur.execute("CREATE TABLE IF NOT EXISTS admin (user_id INTEGER, expire_date TEXT)")
        cur.execute("SELECT * FROM admin WHERE user_id == ?;", (총판.id,))
        admin_result = cur.fetchone()
        con.close()
        
        if admin_result:
            expire_date = admin_result[1]
            if expire_date and not is_expired(expire_date):
                remaining_time = get_expiretime(expire_date)
                await inter.response.send_message(embed=embed("success", "총판 정보", f"총판: {총판.mention}\n만료일: {expire_date}\n남은 기간: {remaining_time}"))
            else:
                await inter.response.send_message(embed=embed("error", "오류", "해당 사용자는 총판이 아니거나 만료된 총판입니다."), ephemeral=True)
        else:
            await inter.response.send_message(embed=embed("error", "오류", "해당 사용자는 총판이 아닙니다."), ephemeral=True)


client.run(settings.token)
