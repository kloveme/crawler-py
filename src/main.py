import re
import time
import catiox
import aiohttp
import asyncio

index_time = 60000
start_time = 30000
query_referer = "https://v.qq.com/"
query_origin = "https://v.qq.com/"
user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0"
content_type = "application/json"
query_video_api = "https://pbaccess.video.qq.com/trpc.videosearch.mobile_search.MultiTerminalSearch/MbSearch?vversion_platform=2"

def slow_bar(total=10, delay=0.1):
    for i in range(total + 1):
        bar = "=" * i + " " * (total - i)
        print(f"\rLOADING CATIOX [{bar}] {i*5}%", end="", flush=True)
        time.sleep(delay)
    catiox.catiox_init(5)
    print()
def parser_video_id(search_json):
    try:
        items = search_json['data']['normalList']['itemList']
    except (KeyError, TypeError):
        print("[ERROR] Data format not match")
        return []
    vids = []
    for item in items:
        try:   
            vid = item['videoInfo']['videoDoc'].get('vid')
            if not vid:
                data_key = item['videoInfo']['videoDoc'].get('dataKey', '')
                match = re.search(r'vid=([a-z0-9]+)', data_key)
                vid = match.group(1) if match else None
            if vid:
                vids.append(vid)
        except (KeyError, TypeError):
            continue
    return vids

async def search_video (video_name):
    print(f"[SEARCH] FIND '{video_name}'");
    query_headers = {
            "referer" : query_referer,
            "origin" : query_origin,
            "content-type" : content_type,
            "user-agent" : user_agent
            }
    query_body = {
            "version":"26022601",
            "clientType":"1",
            "query":video_name,
            "pagenum":"0",
            "pagesize":"30"
            }

    async with aiohttp.ClientSession() as client_session:
        async with client_session.post(url=query_video_api , headers=query_headers , json=query_body) as resp:
            if (resp.status == 200):
                print(f"[SEARCH] Search {video_name} OK");
                return await resp.json()
            return None
        return None

def io_callback_func (file_name) :
    def on_save_failur (error_message) :
        print(f"[FAILED] Save {file_name} failed | Error {error_message}|")
        exit()
    def on_save_success (bytes) :
        print(f"[SUCCESS] Save {file_name} success | Write {bytes} bytes|")
    return on_save_failur , on_save_success

async def get_video_id (name):
    res = await search_video(name);
    return res;

async def request(s_t , end_t , video_id):    
    url_ = f"https://dm.video.qq.com/barrage/segment/{video_id}/t/v1/{s_t*1000}/{end_t*1000}"
    async with aiohttp.ClientSession() as async_client:
        async with async_client.get(url=url_) as response_:
            if response_.status == 200:
                print(f"[LOG] REQUEST API > {url_} SUCCESS")
                return await response_.json()
            print(f"[ERROR] Request failed | {response_.status}")
        return None

async def make_save_format(res_json , id):
    barrage_list = res_json.get("barrage_list", [])
    for i , item in enumerate(barrage_list):
        id = item.get("id")
        content= item.get("content")
        comment_data = f"""{i}|ID = {id} | CONNENT = {content}
"""
        print(comment_data)
        await save_sb_barrage(comment_data , id)

async def save_sb_barrage (res_data , video_id):
    file_name = f"{video_id}-{time.time() *10}-content.txt"
    print(f"[LOG] Save result to > {file_name}")
    on_save_filur , on_save_success = io_callback_func(file_name)
    async_write = catiox.catiox_async_write(res_data)
    async_write.async_writefile("./content/" ,
        file_name , catiox.write_type.catiox_write_append , 
        on_save_filur , on_save_success)
    await asyncio.sleep(0.06)

async def main () :
    seup = 60 
    slow_bar();
    video_name = input("VIDEO NAME > ")
    search_id_respjson = await get_video_id(video_name);
    for vid in parser_video_id(search_id_respjson) :
        print(f"{vid}")
        for start_ in range(0,index_time,seup):
            end_ = min(start_ + seup , index_time)
            data = await request(start_ , end_ , vid)
            await make_save_format(data , vid)

if __name__ == '__main__':
    asyncio.run(main())
