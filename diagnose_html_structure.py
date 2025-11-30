"""
診斷 Baseball Reference HTML 結構
幫助我們了解實際的頁面結構，以便調整爬蟲
"""

import requests
from bs4 import BeautifulSoup


def diagnose_awards_page():
    """診斷獎項頁面結構"""
    
    url = "https://www.baseball-reference.com/awards/awards_2024.shtml"
    
    print("=" * 80)
    print("診斷獎項頁面結構")
    print("=" * 80)
    print(f"\nURL: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("[1] 檢查所有標題 (h2, h3)")
        print("-" * 80)
        headers = soup.find_all(['h2', 'h3'])
        for i, h in enumerate(headers[:15], 1):  # 只顯示前 15 個
            text = h.get_text(strip=True)
            print(f"{i}. <{h.name}> {text}")
        
        print("\n[2] 檢查所有表格")
        print("-" * 80)
        tables = soup.find_all('table')
        print(f"找到 {len(tables)} 個表格\n")
        
        for i, table in enumerate(tables[:5], 1):  # 只檢查前 5 個表格
            print(f"表格 {i}:")
            
            # 檢查 id 和 class
            table_id = table.get('id', 'N/A')
            table_class = table.get('class', 'N/A')
            print(f"  ID: {table_id}")
            print(f"  Class: {table_class}")
            
            # 檢查前幾行
            rows = table.find_all('tr')[:3]
            print(f"  前 3 行:")
            
            for j, row in enumerate(rows, 1):
                cols = row.find_all(['td', 'th'])
                if cols:
                    first_col = cols[0].get_text(strip=True)
                    print(f"    行 {j}: {first_col} ({'有 data-append-csv' if cols[0].get('data-append-csv') else '無 data-append-csv'})")
            print()
        
        print("[3] 檢查是否有 MVP 相關內容")
        print("-" * 80)
        
        # 嘗試不同的方式找 MVP
        mvp_patterns = [
            soup.find('h2', string=lambda x: x and 'MVP' in x),
            soup.find('h3', string=lambda x: x and 'MVP' in x),
            soup.find(id=lambda x: x and 'mvp' in x.lower() if x else False),
            soup.find('div', {'id': lambda x: x and 'mvp' in x.lower() if x else False})
        ]
        
        for i, pattern in enumerate(mvp_patterns, 1):
            if pattern:
                print(f"✅ 方式 {i} 找到 MVP: {pattern.name} - {pattern.get_text(strip=True)[:50]}")
            else:
                print(f"❌ 方式 {i} 未找到")
        
        print("\n[4] 儲存完整 HTML（用於詳細分析）")
        print("-" * 80)
        with open('awards_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        print("✅ 已儲存到 awards_page_debug.html")
        
        print("\n建議：")
        print("1. 查看 awards_page_debug.html")
        print("2. 搜尋 'MVP' 或 'Cy Young'")
        print("3. 查看表格的 id 和結構")
        print("4. 告訴我你看到的結構")
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()


def diagnose_allstar_urls():
    """測試不同的 All-Star URL 格式"""
    
    print("\n" + "=" * 80)
    print("測試 All-Star URL 格式")
    print("=" * 80)
    
    base_url = "https://www.baseball-reference.com"
    
    # 可能的 URL 格式
    url_patterns = [
        "/allstar/AL-{year}-All-Star-Team-roster.shtml",
        "/allstar/{year}-All-Star-Game.shtml",
        "/allstar/MLB_{year}_All-Star_Game.shtml",
        "/allstar/{year}AllStarGame.shtml",
    ]
    
    year = 2024
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for pattern in url_patterns:
        url = base_url + pattern.format(year=year)
        print(f"\n測試: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ 成功 (200)")
                
                # 檢查是否有 All-Star 相關內容
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                if title:
                    print(f"  頁面標題: {title.get_text(strip=True)[:60]}")
            elif response.status_code == 404:
                print(f"  ❌ 404 Not Found")
            else:
                print(f"  ⚠️  {response.status_code}")
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")


if __name__ == "__main__":
    # 診斷獎項頁面
    diagnose_awards_page()
    
    # 測試 All-Star URLs
    diagnose_allstar_urls()
    
    print("\n" + "=" * 80)
    print("診斷完成")
    print("=" * 80)
    print("\n下一步：")
    print("1. 查看 awards_page_debug.html")
    print("2. 告訴我你看到的結構")
    print("3. 我會根據實際結構調整爬蟲")
