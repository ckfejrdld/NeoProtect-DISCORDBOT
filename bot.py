import discord
import sqlite3
import config
import api
import asyncio
import datetime
import json

client = discord.Client(intents=discord.Intents.all())

def create_table():
    con = connect_db()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS proxy (
        "domain"	TEXT NOT NULL,
        "backend"	TEXT NOT NULL,
        "owner"	TEXT NOT NULL,
        "created_at" TEXT
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS backend (
        "name"	TEXT NOT NULL,
        "hostname"	TEXT NOT NULL,
        "port"	INTEGER NOT NULL,
        "proxy_protocol"	INTEGER NOT NULL,
        "groupId"	TEXT NOT NULL,
        "owner"	TEXT NOT NULL,
        "created_at" TEXT
    );""")
    con.commit()
    con.close()

def connect_db():
    return sqlite3.connect("database.db")

@client.event
async def on_ready():
    create_table()
    await client.change_presence(activity=discord.Game(name="p! 도움말"))
    print(f"{client.user.name} is on ready.")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith(f"{config.bot_prefix} "):
        if not isinstance(message.channel, discord.channel.DMChannel):
            msg = await message.reply("DM에서 진행해주세요.")
            await asyncio.sleep(5)
            await msg.delete()
            return
        split = message.content.split(" ")
        if split[1] == "도움말" or split[1] == "help":
            embed = discord.Embed(title="도움말", description="nPerm Proxy 도움말을 확인합니다.", color=0x62c1cc)
            embed.add_field(name=f"{config.bot_prefix} 도메인 등록 [도메인] [백엔드 서버 ID]", value="nPerm Proxy를 도메인에 등록합니다.", inline=False)
            embed.add_field(name=f"{config.bot_prefix} 도메인 삭제 [도메인]", value="nPerm Proxy를 도메인에서 제거합니다.", inline=False)
            embed.add_field(name=f"{config.bot_prefix} 백엔드 등록 [백엔드 서버 이름] [아이피/도메인] [포트] [프록시 프로토콜 여부(on/off)]", value="백엔드 서버를 등록합니다.", inline=False)
            embed.add_field(name=f"{config.bot_prefix} 백엔드 삭제 [백엔드 서버 ID]", value="백엔드 서버를 삭제합니다.", inline=False)
            await message.reply(embed=embed)
    
        elif split[1] == "도메인":
            if split[2] == "등록":
                con = connect_db()
                cur = con.cursor()
                cur.execute("SELECT owner FROM `proxy` WHERE domain = ?", (split[3],))
                data = cur.fetchone()
                con.close()
                if data:
                    await message.reply("이미 등록된 도메인입니다.")
                    return
                else:
                    con = connect_db()
                    cur = con.cursor()
                    cur.execute("SELECT hostname FROM backend WHERE groupId = ? AND owner = ?", (split[4], message.author.id,))
                    data = cur.fetchone()
                    con.close()
                    if data:
                        if api.verify_domain(split[3]) == True:
                            if api.create_domain(config.GameShieldsId, split[3]) == 200:
                                set_backend_to_domain = api.set_backend_to_domain(split[3], split[4])
                                if set_backend_to_domain == 200:
                                    con = connect_db()
                                    cur = con.cursor()
                                    cur.execute("INSERT INTO `proxy` VALUES(?, ?, ?, ?);", (split[3], split[4], message.author.id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%H"),))
                                    con.commit()
                                    con.close()
                                    await message.reply("성공적으로 등록되었습니다.")
                                else:
                                    print(set_backend_to_domain)
                                    await message.reply("오류가 발생했습니다. 명령어를 다시 확인해주세요.")
                            else:
                                await message.reply("오류가 발생했습니다. 명령어를 다시 확인해주세요.")
                        else:
                            await message.reply("인증된 도메인이 아닙니다. 인증 후 다시 시도해주세요.")
                    else:
                        await message.reply("존재하지 않거나 본인이 등록하지 않은 백엔드 서버입니다.")
            elif split[2] == "삭제":
                con = connect_db()
                cur = con.cursor()
                cur.execute("SELECT backend FROM proxy WHERE domain = ? AND owner = ?", (split[3], message.author.id),)
                data = cur.fetchone()
                con.close()
                if data:
                    delete_domain = api.delete_domain(split[3])
                    if delete_domain == 200:
                        con = connect_db()
                        cur = con.cursor()
                        cur.execute("DELETE FROM `proxy` WHERE domain = ?;", (split[3],))
                        con.commit()
                        con.close()
                        await message.reply("성공적으로 삭제되었습니다.")
                    else:
                        print(delete_domain)
                        await message.reply("오류가 발생했습니다. 관리자에게 문의하세요.")
                else:
                    await message.reply("등록되지 않았거나 본인이 소유하지 않은 도메인입니다.")
                    return
            elif split[2] == "목록":
                con = connect_db()
                cur = con.cursor()
                cur.execute("SELECT domain FROM proxy WHERE owner = ?", (message.author.id,))
                data = cur.fetchall()
                con.close()
                data = [j for i in data for j in i]
                embed = discord.Embed(title="도메인 목록", description="nPerm Proxy에 등록된 도메인 목록을 확인합니다.", color=0x62c1cc)
                for i in data:
                    embed.add_field(name="", value=i, inline=False)
                await message.reply(embed=embed)

        elif split[1] == "백엔드":
            if split[2] == "등록":
                con = connect_db()
                cur = con.cursor()
                cur.execute("SELECT COUNT(hostname) FROM `backend` WHERE owner = ?", (message.author.id,))
                count_data = cur.fetchone()
                con.close()
                for i in count_data:
                    count = int(i)
                if count >= config.maximum_backend_count:
                    await message.reply("백엔드 서버 등록 가능 최대 한도를 초과하셨습니다.")
                    return
                if split[6] not in ["on", "off"]:
                    await message.reply("Proxy Protocol 여부는 on/off 중으로 작성해주세요.")
                    return
                try:
                    port = int(split[5])
                    if port < 1 or port > 65536:
                        await message.reply("포트는 1~65535 중으로 선택해주세요.")
                        return
                except:
                    await message.reply("포트는 1~65535 중으로 선택해주세요.")
                    return
                if split[6] == "on":
                    proxyprotocol = True
                    proxy_protocol_status = 1
                elif split[6] == "off":
                    proxyprotocol = False
                    proxy_protocol_status = 0
                create_backend_group, create_backend_status = api.create_backend_group(config.GameShieldsId, split[3], "random", proxyprotocol, False, "japan")
                create_backend_group = json.loads(create_backend_group)
                if create_backend_status == 200:
                    if api.create_backend(config.GameShieldsId, create_backend_group["id"], split[4], port) == 200:
                        con = connect_db()
                        cur = con.cursor()
                        cur.execute("INSERT INTO `backend` VALUES(?, ?, ?, ?, ?, ?, ?);", (split[3], split[4], port, proxy_protocol_status, create_backend_group["id"], message.author.id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%H"),))
                        con.commit()
                        con.close()
                        await message.reply(f"백엔드 서버가 성공적으로 생성되었습니다. | 백엔드 서버 ID: {create_backend_group['id']}")
                    else:
                        await message.reply("백엔드 서버 생성 중 오류가 발생했습니다.")
                else:
                    await message.reply("백엔드 서버 생성 중 오류가 발생했습니다.")
                        
            elif split[2] == "삭제":
                con = connect_db()
                cur = con.cursor()
                cur.execute("SELECT groupId FROM `backend` WHERE groupId = ? AND owner = ?", (split[3], message.author.id),)
                data = cur.fetchone()
                con.close()
                if data:
                    if api.delete_backend_group(config.GameShieldsId, split[3]) == 200:
                        con = connect_db()
                        cur = con.cursor()
                        cur.execute("DELETE FROM `backend` WHERE groupId = ?;", (split[3],))
                        con.commit()
                        con.close()
                        await message.reply("성공적으로 삭제되었습니다.")
                    else:
                        await message.reply("오류가 발생했습니다. 관리자에게 문의하세요.")
                else:
                    await message.reply("등록되지 않았거나 본인이 소유하지 않은 백엔드 서버입니다.")
                    return

            elif split[2] == "목록":
                con = connect_db()
                cur = con.cursor()
                cur.execute("SELECT name,hostname,port,proxy_protocol,groupId FROM `backend` WHERE owner = ?", (message.author.id,))
                data = cur.fetchall()
                con.close()
                embed = discord.Embed(title="백엔드 서버 목록", description="nPerm Proxy에 등록된 백엔드 서버 목록을 확인합니다.", color=0x62c1cc)
                for i in data:
                    name, hostname, port, proxyprotocol_status, groupId = i
                    if proxyprotocol_status == 0:
                        proxy_protocol = "off"
                    if proxyprotocol_status == 1:
                        proxy_protocol = "on"
                    embed.add_field(name=name, value=f"{hostname}:{port} - Proxy Protocol: {proxy_protocol} - Backend ID: {groupId}", inline=False)
                await message.reply(embed=embed)

client.run(config.bot_token)