'''
This script retrieves and displays MLB player statistics.
'''
import pybaseball

def get_player_stats(player_name):
    """
    Retrieves and displays batting statistics for a given player.

    Args:
        player_name (str): The full name of the player.
    """
    try:
        # Step 1: Player ID Lookup
        player_info = pybaseball.playerid_lookup(last=player_name.split(' ')[-1], first=player_name.split(' ')[0])
        if player_info.empty:
            print(f"Player '{player_name}' not found.")
            return

        # Get the MLB key for the first player found
        player_id = player_info['key_mlbam'].iloc[0]

        # Step 2: Fetching Core Stats (Batting)
        # Fetching career batting stats
        batting_data = pybaseball.batting_stats(player_id, stat_group='hitting', qual=1)

        if batting_data.empty:
            print(f"No batting stats found for {player_name}.")
            return

        # Get the most recent season's stats
        latest_stats = batting_data.loc[batting_data['Season'] == batting_data['Season'].max()]

        # Step 3: Displaying the data
        print(f"--- Batting Stats for {player_name} ({latest_stats['Season'].iloc[0]}) ---")
        print(f"{ 'PA':<5} | {'AB':<5} | {'H':<5} | {'HR':<5} | {'RBI':<5} | {'AVG':<5}")
        print("-" * 40)
        print(f"{latest_stats['PA'].iloc[0]:<5} | {latest_stats['AB'].iloc[0]:<5} | {latest_stats['H'].iloc[0]:<5} | {latest_stats['HR'].iloc[0]:<5} | {latest_stats['RBI'].iloc[0]:<5} | {latest_stats['AVG'].iloc[0]:.3f}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example: Get stats for Shohei Ohtani
    get_player_stats("Shohei Ohtani")
