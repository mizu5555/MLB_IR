"""
Phase 4: Baseball Savant Statcast 數據下載
從 Baseball Savant Leaderboard 下載 CSV 數據
"""

import requests
import pandas as pd
import time
from typing import Dict, List
import json


class BaseballSavantDownloader:
    """Baseball Savant 數據下載器"""
    
    def __init__(self):
        self.base_url = "https://baseballsavant.mlb.com/leaderboard/custom"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def download_batter_statcast(self, year: int) -> pd.DataFrame:
        """
        下載打者 Statcast 數據
        
        Args:
            year: 年份
        
        Returns:
            DataFrame with batter Statcast data
        """
        
        print(f"\n下載 {year} 打者 Statcast 數據...")
        
        # Baseball Savant Leaderboard 參數
        params = {
            'year': year,
            'type': 'batter',
            'filter': '',
            'sort': 'pa',
            'sortDir': 'desc',
            'min': 50,  # 最少 50 PA
            'selections': 'xba,xslg,xwoba,exit_velocity_avg,launch_angle_avg,barrel_batted_rate,hard_hit_percent,sprint_speed',
            'chart': 'false',
            'x': 'xba',
            'y': 'xslg',
            'r': 'no',
            'chartType': 'beeswarm',
        }
        
        try:
            # 構建 URL
            url = f"{self.base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            
            print(f"  URL: {url[:100]}...")
            
            # 發送請求
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # 解析 CSV（Baseball Savant 返回 CSV 格式）
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            print(f"  ✅ 成功下載 {len(df)} 位打者")
            
            # 重命名欄位（統一格式）
            column_mapping = {
                'last_name, first_name': 'player_name',
                'pa': 'PA',
                'exit_velocity_avg': 'exit_velocity',
                'launch_angle_avg': 'launch_angle',
                'barrel_batted_rate': 'barrel_rate',
                'hard_hit_percent': 'hard_hit_rate',
            }
            
            df = df.rename(columns=column_mapping)
            
            # 添加年份
            df['year'] = year
            
            return df
            
        except Exception as e:
            print(f"  ❌ 下載失敗: {e}")
            return pd.DataFrame()
    
    def download_pitcher_statcast(self, year: int) -> pd.DataFrame:
        """
        下載投手 Statcast 數據
        
        Args:
            year: 年份
        
        Returns:
            DataFrame with pitcher Statcast data
        """
        
        print(f"\n下載 {year} 投手 Statcast 數據...")
        
        params = {
            'year': year,
            'type': 'pitcher',
            'filter': '',
            'sort': 'ip',
            'sortDir': 'desc',
            'min': 20,  # 最少 20 IP
            'selections': 'fastball_avg_speed,fastball_avg_spin,whiff_percent,chase_percent,barrel_batted_rate,hard_hit_percent',
            'chart': 'false',
            'x': 'fastball_avg_speed',
            'y': 'whiff_percent',
            'r': 'no',
            'chartType': 'beeswarm',
        }
        
        try:
            url = f"{self.base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            
            print(f"  URL: {url[:100]}...")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            print(f"  ✅ 成功下載 {len(df)} 位投手")
            
            # 重命名欄位
            column_mapping = {
                'last_name, first_name': 'player_name',
                'ip': 'IP',
                'fastball_avg_speed': 'fastball_velocity',
                'fastball_avg_spin': 'fastball_spin',
                'whiff_percent': 'whiff_rate',
                'chase_percent': 'chase_rate',
                'barrel_batted_rate': 'barrel_rate_against',
                'hard_hit_percent': 'hard_hit_rate_against',
            }
            
            df = df.rename(columns=column_mapping)
            
            # 添加年份
            df['year'] = year
            
            return df
            
        except Exception as e:
            print(f"  ❌ 下載失敗: {e}")
            return pd.DataFrame()
    
    def download_all_years(self, years: List[int]) -> Dict:
        """
        下載多年數據
        
        Args:
            years: 年份列表
        
        Returns:
            字典包含打者和投手數據
        """
        
        print("=" * 80)
        print("Phase 4: Baseball Savant Statcast 數據下載")
        print("=" * 80)
        
        all_batters = []
        all_pitchers = []
        
        for year in years:
            # 下載打者數據
            batters_df = self.download_batter_statcast(year)
            if not batters_df.empty:
                all_batters.append(batters_df)
            
            time.sleep(3)  # 禮貌性延遲
            
            # 下載投手數據
            pitchers_df = self.download_pitcher_statcast(year)
            if not pitchers_df.empty:
                all_pitchers.append(pitchers_df)
            
            time.sleep(3)
        
        # 合併所有年份
        batters_combined = pd.concat(all_batters, ignore_index=True) if all_batters else pd.DataFrame()
        pitchers_combined = pd.concat(all_pitchers, ignore_index=True) if all_pitchers else pd.DataFrame()
        
        print("\n" + "=" * 80)
        print("下載完成")
        print("=" * 80)
        print(f"打者數據: {len(batters_combined)} 筆記錄")
        print(f"投手數據: {len(pitchers_combined)} 筆記錄")
        
        return {
            'batters': batters_combined,
            'pitchers': pitchers_combined
        }
    
    def save_data(self, data: Dict, output_dir: str = './mlb_data'):
        """
        儲存數據
        
        Args:
            data: 包含打者和投手數據的字典
            output_dir: 輸出目錄
        """
        
        print("\n" + "=" * 80)
        print("儲存數據")
        print("=" * 80)
        
        # 儲存 CSV（原始格式）
        if not data['batters'].empty:
            csv_file = f"{output_dir}/statcast_batters_raw.csv"
            data['batters'].to_csv(csv_file, index=False, encoding='utf-8')
            print(f"✅ 打者 CSV: {csv_file}")
        
        if not data['pitchers'].empty:
            csv_file = f"{output_dir}/statcast_pitchers_raw.csv"
            data['pitchers'].to_csv(csv_file, index=False, encoding='utf-8')
            print(f"✅ 投手 CSV: {csv_file}")
        
        # 轉換為 JSON 格式（用於整合）
        batters_json = self._convert_to_json_format(data['batters'], 'batter')
        pitchers_json = self._convert_to_json_format(data['pitchers'], 'pitcher')
        
        # 儲存 JSON
        output_file = f"{output_dir}/week5_statcast.json"
        combined_json = {**batters_json, **pitchers_json}
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_json, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON: {output_file}")
        print(f"   總球員數: {len(combined_json)}")
    
    def _convert_to_json_format(self, df: pd.DataFrame, player_type: str) -> Dict:
        """
        轉換 DataFrame 為 JSON 格式
        
        Args:
            df: DataFrame
            player_type: 'batter' or 'pitcher'
        
        Returns:
            字典格式的數據
        """
        
        if df.empty:
            return {}
        
        result = {}
        
        # 按球員和年份分組
        for _, row in df.iterrows():
            # 處理球員名字格式："Last, First" → "First Last"
            name = row.get('player_name', '')
            if ',' in name:
                last, first = name.split(',', 1)
                full_name = f"{first.strip()} {last.strip()}"
            else:
                full_name = name
            
            year = row.get('year', 2024)
            key = f"{full_name}_{year}"
            
            if player_type == 'batter':
                result[key] = {
                    'player_name': full_name,
                    'year': int(year),
                    'type': 'batter',
                    'exit_velocity': float(row.get('exit_velocity', 0)) if pd.notna(row.get('exit_velocity')) else None,
                    'launch_angle': float(row.get('launch_angle', 0)) if pd.notna(row.get('launch_angle')) else None,
                    'barrel_rate': float(row.get('barrel_rate', 0)) if pd.notna(row.get('barrel_rate')) else None,
                    'hard_hit_rate': float(row.get('hard_hit_rate', 0)) if pd.notna(row.get('hard_hit_rate')) else None,
                    'xba': float(row.get('xba', 0)) if pd.notna(row.get('xba')) else None,
                    'xslg': float(row.get('xslg', 0)) if pd.notna(row.get('xslg')) else None,
                    'xwoba': float(row.get('xwoba', 0)) if pd.notna(row.get('xwoba')) else None,
                    'sprint_speed': float(row.get('sprint_speed', 0)) if pd.notna(row.get('sprint_speed')) else None,
                }
            else:  # pitcher
                result[key] = {
                    'player_name': full_name,
                    'year': int(year),
                    'type': 'pitcher',
                    'fastball_velocity': float(row.get('fastball_velocity', 0)) if pd.notna(row.get('fastball_velocity')) else None,
                    'fastball_spin': float(row.get('fastball_spin', 0)) if pd.notna(row.get('fastball_spin')) else None,
                    'whiff_rate': float(row.get('whiff_rate', 0)) if pd.notna(row.get('whiff_rate')) else None,
                    'chase_rate': float(row.get('chase_rate', 0)) if pd.notna(row.get('chase_rate')) else None,
                    'barrel_rate_against': float(row.get('barrel_rate_against', 0)) if pd.notna(row.get('barrel_rate_against')) else None,
                    'hard_hit_rate_against': float(row.get('hard_hit_rate_against', 0)) if pd.notna(row.get('hard_hit_rate_against')) else None,
                }
        
        return result


def main():
    """主程式"""
    
    print("\n" + "=" * 80)
    print("Phase 4: Baseball Savant Statcast 數據下載")
    print("=" * 80)
    
    # 設定年份
    years = [2022, 2023, 2024]
    
    print(f"\n準備下載 {years} 年份的 Statcast 數據...")
    print("這可能需要 5-10 分鐘...\n")
    
    # 建立下載器
    downloader = BaseballSavantDownloader()
    
    try:
        # 下載數據
        data = downloader.download_all_years(years)
        
        # 儲存數據
        downloader.save_data(data)
        
        # 顯示統計
        print("\n" + "=" * 80)
        print("數據統計")
        print("=" * 80)
        
        if not data['batters'].empty:
            print("\n打者 Statcast 前 5 位（按 exit velocity）:")
            top_batters = data['batters'].nlargest(5, 'exit_velocity')
            for i, row in enumerate(top_batters.itertuples(), 1):
                name = row.player_name
                ev = row.exit_velocity
                year = row.year
                print(f"  {i}. {name} ({year}): {ev:.1f} mph")
        
        if not data['pitchers'].empty:
            print("\n投手 Statcast 前 5 位（按 fastball velocity）:")
            top_pitchers = data['pitchers'].nlargest(5, 'fastball_velocity')
            for i, row in enumerate(top_pitchers.itertuples(), 1):
                name = row.player_name
                velo = row.fastball_velocity
                year = row.year
                print(f"  {i}. {name} ({year}): {velo:.1f} mph")
        
        print("\n" + "=" * 80)
        print("✨ 下載完成！")
        print("=" * 80)
        print("\n下一步：")
        print("  python week5_integrate_statcast.py  (整合 Statcast 數據)")
        
    except KeyboardInterrupt:
        print("\n\n下載被中斷")
    except Exception as e:
        print(f"\n\n❌ 下載失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
