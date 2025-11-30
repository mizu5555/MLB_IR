"""
診斷 Baseball Savant 返回內容
"""

import requests


def diagnose_baseball_savant():
    """診斷 Baseball Savant API"""
    
    print("=" * 80)
    print("診斷 Baseball Savant API")
    print("=" * 80)
    
    # 測試 URL
    base_url = "https://baseballsavant.mlb.com/leaderboard/custom"
    
    params = {
        'year': 2024,
        'type': 'batter',
        'filter': '',
        'sort': 'pa',
        'sortDir': 'desc',
        'min': 50,
        'selections': 'xba,xslg,xwoba,exit_velocity_avg,launch_angle_avg,barrel_batted_rate,hard_hit_percent,sprint_speed',
        'chart': 'false',
        'x': 'xba',
        'y': 'xslg',
        'r': 'no',
        'chartType': 'beeswarm',
    }
    
    url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    print(f"\nURL: {url}")
    print("\n發送請求...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content Length: {len(response.text)} bytes")
        
        # 檢查前 1000 個字符
        print("\n前 1000 個字符:")
        print("-" * 80)
        print(response.text[:1000])
        print("-" * 80)
        
        # 儲存完整內容
        with open('baseball_savant_response.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print("\n✅ 完整內容已儲存到 baseball_savant_response.txt")
        
        # 檢查是否是 CSV
        if ',' in response.text[:500]:
            print("\n可能是 CSV 格式")
            lines = response.text.split('\n')
            print(f"總行數: {len(lines)}")
            print("\n前 5 行:")
            for i, line in enumerate(lines[:5], 1):
                print(f"{i}. {line[:100]}")
        else:
            print("\n⚠️  可能不是 CSV 格式")
        
        # 檢查是否是 JSON
        if response.text.strip().startswith('{') or response.text.strip().startswith('['):
            print("\n可能是 JSON 格式")
            import json
            try:
                data = json.loads(response.text)
                print(f"JSON 鍵: {list(data.keys()) if isinstance(data, dict) else 'List'}")
            except:
                print("JSON 解析失敗")
        
        # 檢查是否是 HTML
        if '<html' in response.text.lower() or '<!doctype' in response.text.lower():
            print("\n⚠️  返回的是 HTML 頁面")
            print("建議：需要使用不同的 API endpoint 或方法")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    diagnose_baseball_savant()
    
    print("\n" + "=" * 80)
    print("建議:")
    print("=" * 80)
    print("\n1. 查看 baseball_savant_response.txt")
    print("2. 告訴我前 1000 個字符的內容")
    print("3. 我會根據實際格式調整腳本")
    print("\n或者，我們可以改用 pybaseball 的 statcast 功能（更可靠）")
