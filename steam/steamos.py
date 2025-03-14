from http.client import responses
from urllib import request
import requests
from steam.steamid import SteamID
import steam.steamid
from steam.webapi import WebAPI
import certifi
import json
import os
from datetime import datetime
import steam
import yaml
import sys


# 读取 config.yaml
def load_config():
    try:
        # 判断是否是打包环境
        if getattr(sys, 'frozen', False):
            # 打包后获取 EXE 所在目录
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境获取脚本所在目录
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 组合配置文件路径
        config_path = os.path.join(base_path, "config.yaml")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # 提取 vanity_url
        vanity_url = config["steam_id"]
        
        return {
            "API_KEY": config["steam_api_key"],
            "VANITY_URL": vanity_url
        }
    
    except FileNotFoundError:
        print("错误：未找到 config.yaml 文件，请确保它和 EXE 在同一目录")
        sys.exit(1)
    except KeyError as e:
        print(f"错误：config.yaml 中缺少必要的键 {e}")
        sys.exit(1)





def validate_response(response):
    """验证 API 响应结构"""
    if response.status_code != 200:
        return False, f"HTTP 错误: {response.status_code}"
    
    data = response.json()
    if "response" not in data:
        return False, "响应缺少 'response' 字段"
    
    games = data["response"].get("games", [])
    if not games:
        return False, "游戏列表为空（用户可能未公开游戏库）"
    
    # 检查首个游戏的数据完整性
    sample_game = games[0]
    required_fields = ["appid", "name", "playtime_forever"]
    for field in required_fields:
        if field not in sample_game:
            return False, f"游戏数据缺少 '{field}' 字段"
    
    return True, "数据验证通过"

def resolve_vanity_to_steamid(vanity_url: str):
    """
    将Steam自定义URL转换为SteamID对象
    
    :param api_key: Steam Web API密钥
    :param vanity_url: 用户自定义URL标识（如'valve'对应https://steamcommunity.com/id/valve）
    :return: SteamID对象
    :raises: WebAPIException 当API调用失败时
    :raises: ValueError 当无法解析自定义URL时
    """

    steam_id = steam.steamid.from_url(vanity_url)
    
    
    return steam_id

def get_game(api_key, steamid):
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    params = {
        "key": api_key,
        "steamid": steamid,
        "include_appinfo": 1,
        "include_played_free_games": 1,
    }

    try:
        # 发起请求
        response = requests.get(url=url, params=params, verify=certifi.where())
        # 验证响应数据
        is_valid, message = validate_response(response)
        if not is_valid:
            print(f"数据异常: {message}")
            return
        
        games = response.json()["response"]["games"]
        return games   

    except Exception as e:
        print(f"请求错误：{str(e)}")


def games_response(games):
    games = games
    game_list = [
        {
             "游戏名称": game.get('name', '未知游戏'),
            "游戏时长": f"{game.get('playtime_forever', 0)//60}小时{game.get('playtime_forever', 0)%60}分钟"
        }
        for game in games 

    ]

    return game_list
    
def save_games_list(games_list):
    # 定義保存路徑
    save_dir = os.path.join(os.getcwd(), 'output')  # 保存到當前目錄的output文件夾
    file_name = f"steam_games_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    file_path = os.path.join(save_dir, file_name)
    
    try:
        # 創建目錄（如果不存在）
        os.makedirs(save_dir, exist_ok=True)
        
        # 檢查數據是否有效
        if not games_list:
            print("警告: 遊戲列表為空，未寫入文件。")
            return
        
        # 寫入JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(games_list, f, ensure_ascii=False, indent=4)
            
        print(f"✅ 數據已保存至: {file_path}")
    
    except PermissionError:
        print("❌ 錯誤: 沒有文件寫入權限，請檢查路徑或權限設置。")
    except Exception as e:
        print(f"❌ 未知錯誤: {str(e)}")
           


if __name__ == "__main__":
        # 加载配置
        config = load_config()
        API_KEY = config["API_KEY"]
        VANITY_URL = config["VANITY_URL"]
        steam_id = resolve_vanity_to_steamid(VANITY_URL)
        games = get_game(api_key=API_KEY,steamid=steam_id)
        games_list = games_response(games=games)
        save_games_list(games_list=games_list)