import streamlit as st
import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

###################################
#
# Lichess Game Metrics Explorer
# with Streamlit, version 1.23.1
#
# @author Amir
#
###################################

@st.cache_data(ttl=600) # cache data for 10 minutes (=600 seconds)
def get_game_metrics(username, game_mode):
    """
    Get the metrics: number of games, wins, draws and losses
    
    Arguments:
        username: a Lichess username
        game_mode: a game mode, e.g., "blitz"

    Returns:
        the metrics if the request was successful, otherwise None
    """
    url = f"https://lichess.org/api/user/{username}/perf/{game_mode}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        games_played = data["stat"]["count"]["all"]
        wins = data["stat"]["count"]["win"]
        draws = data["stat"]["count"]["draw"]
        losses = data["stat"]["count"]["loss"]
        return games_played, wins, draws, losses
    else:
        return None, None, None, None

# def get_total_wins(username):
#     url = f"https://lichess.org/api/user/{username}"
#     response = requests.get(url)
#     if response.status_code == 200:
#         data = response.json()
#         return data["count"]["win"]
#     else:
#         return None


def pgn_to_dataframe(pgn_file):
    """
    Convert a PGN file to a Pandas DataFrame (except the actual moves)

    Arguments:
        pgn_file: a PGN file of a chess game

    Returns:
        a Pandas DataFrame
    """
    games_data = [] # for np: np.empty((0,), dtype=object)
    game_lines = pgn_file.split("\n\n\n")
    game_lines = game_lines[:-1]
    
    for game in game_lines:
        game_info = {}
        lines = game.split("\n")

        for line in lines:
            if "[" in line and "]" in line:
                key, value = line.split("[")[1].split("]")[0].split(" \"")
                game_info[key.strip()] = value.strip(" \"")

        games_data.append(game_info) # for np: np.append(games_data, game_info)

    return pd.DataFrame(games_data) # for np: pd.DataFrame(games_data.tolist())

# def extract_openings_from_pgn(pgn_text):
#     openings = []
#     pgn_lines = pgn_text.split("\n")

#     for line in pgn_lines:
#         if "[Opening \"" in line:
#             opening = line.split("[Opening \"")[1].split("\"]")[0]
#             openings.append(opening)

#     return openings


@st.cache_data(ttl=3600) # cache data for 1 hour (=3600 seconds)
def get_most_favorite_openings(username, game_modes):
    """
    Get most favorite openings for each game mode 
    as white and black based on the number of games played

    Arguments:
        username: a Lichess username
        game_modes: all game modes

    Returns:
        a Pandas DataFrame
    """
    favorite_openings_df = pd.DataFrame(columns=["Game Mode", "Piece", "Opening", "Games Played"])

    piece_colors = np.array(["white", "black"])
    top_n = 5 # top n favorite openings

    for mode in game_modes:
        for color in piece_colors:
            url = f"https://lichess.org/api/games/user/{username}?opening=true&color={color}&perfType={mode}&since=1672527600000"
            response = requests.get(url)

            if response.status_code == 200:
                pgn_text = response.text
                pgn_dataframe = pgn_to_dataframe(pgn_text)
                if not pgn_dataframe.empty:
                    top_openings = pgn_dataframe["Opening"].value_counts().head(top_n)
                    openings_df = pd.DataFrame({
                        "Game Mode": [mode] * top_n,
                        "Piece": [color] * top_n,
                        "Opening": top_openings.index.tolist(),
                        "Games Played": top_openings.values.tolist()
                    })
                    favorite_openings_df = pd.concat([favorite_openings_df, openings_df])
                # else:
                #     st.info(f"No openings available as {color} in {mode} mode")

            else:
                st.error(f"Failed to retrieve data for openings as {color} in {mode} mode.")

    favorite_openings_df.reset_index(drop=True, inplace=True)
    return favorite_openings_df


def visualize_metrics(username, game_modes, metrics):
    """
    Visualize metrics by creating a grouped bar plot

    Arguments:
        username: a Lichess username
        game_modes: all game modes
        metrics: all metrics

    Returns:
        a grouped bar plot
    """
    # plt.style.use('ggplot')  # applying the "ggplot" style
    fig, ax = plt.subplots() # fig, ax = plt.subplots(figsize=(10, 6))
    bar_width = 0.2
    index = range(len(game_modes))
    colors = ['blue', 'green', 'orange', 'red']

    for i, metric in enumerate(metrics):
        ax.bar([idx + i * bar_width for idx in index], metrics[metric], bar_width, label=metric, color=colors[i])

    ax.set_title(f"Game Metrics for {username} per Game Mode")
    ax.set_xlabel("Game Mode")
    ax.set_ylabel("Number of Games")
    ax.set_xticks([idx + bar_width for idx in index])
    ax.set_xticklabels(game_modes)
    ax.legend()

    st.pyplot(fig)


def visualize_most_favorite_openings(username, most_favorite_openings_df):
    """
    Visualize most favorite openings as white and black 
    by creating a bar plot for each game mode

    Arguments:
        username: a Lichess username
        most_favorite_openings_df: a Pandas DataFrame returned by function 'get_most_favorite_openings'

    Returns:
        a bar plot for each game mode
    """
    game_modes = most_favorite_openings_df['Game Mode'].unique()

    fig, ax = plt.subplots(len(game_modes), 1, figsize=(10, 10 * len(game_modes)), sharex=False, gridspec_kw={"hspace": 1})
    # plt.xticks(rotation=45, ha="right")

    for idx, mode in enumerate(game_modes):
        mode_df = most_favorite_openings_df[most_favorite_openings_df["Game Mode"] == mode]
        x = list(range(len(mode_df)))

        # separate white and black bars
        white_openings = mode_df[mode_df["Piece"] == "white"]
        black_openings = mode_df[mode_df["Piece"] == "black"]

        ax[idx].bar(x[:len(white_openings)], white_openings["Games Played"], align="center", color='lightgrey')
        ax[idx].bar(x[len(white_openings):], black_openings["Games Played"], align="center", color='black')

        all_openings = white_openings["Opening"].tolist() + black_openings["Opening"].tolist()
        all_labels = all_openings[:len(white_openings)] + all_openings[len(white_openings):]
        
        ax[idx].set_title(f"Most Favorite Openings for {username} in {mode} mode as white and black")
        ax[idx].set_xticks(x)
        ax[idx].set_xticklabels(all_labels, rotation=45, ha='right')
        ax[idx].set_xlabel("Openings")
        ax[idx].set_ylabel("Number of Games")
        ax[idx].grid(axis="y")

    plt.tight_layout()
    st.pyplot(fig)


######################################################

def main():
    
    st.title("Lichess Game Metrics Explorer")

    add_selectbox = st.sidebar.selectbox("Choose an option:", ("All Game Modes","Individual Game Modes"))

    username = st.text_input("Enter the Lichess username of the player:")
    game_modes = np.array(["ultraBullet", "bullet", "blitz", "rapid", "classical"])

    if add_selectbox == "All Game Modes":
        if st.button("Get Metrics"):
            if username:
                metrics = {metric: np.array([]) for metric in ["Games Played", "Wins", "Draws", "Losses"]}
                for mode in game_modes:
                    game_played, wins, draws, losses = get_game_metrics(username, mode)
                    if game_played is not None:
                        metrics["Games Played"] = np.append(metrics["Games Played"], game_played)
                        metrics["Wins"] = np.append(metrics["Wins"], wins)
                        metrics["Draws"] = np.append(metrics["Draws"], draws)
                        metrics["Losses"] = np.append(metrics["Losses"], losses)
                    else:
                        st.error(f"Failed to retrieve data for {username}. Please check the username.")
                        return

                st.success(f"Metrics for {username} fetched successfully!")
                st.write("**Metrics** for All Game Modes for _All Time_:")

                visualize_metrics(username, game_modes, metrics)

                st.write(f"**Most Favorite Openings** in each Game Mode as white and black _since the beginning of 2023_:")

                most_favorite_openings_df = get_most_favorite_openings(username, game_modes)

                visualize_most_favorite_openings(username, most_favorite_openings_df)

                for mode in game_modes:
                    if mode not in most_favorite_openings_df["Game Mode"].unique():
                        st.info(f"No openings available in {mode} mode")
            else:
                st.warning("Please enter a Lichess username.")
    
    if add_selectbox == "Individual Game Modes":

        selected_game_mode = st.selectbox("Select a game mode:", game_modes)

        if st.button("Get Metrics"):
            if username:
                metrics = {metric: np.array([]) for metric in ["Games Played", "Wins", "Draws", "Losses"]}
                for mode in game_modes:
                    game_played, wins, draws, losses = get_game_metrics(username, mode)
                    if game_played is not None:
                        metrics["Games Played"] = np.append(metrics["Games Played"], game_played)
                        metrics["Wins"] = np.append(metrics["Wins"], wins)
                        metrics["Draws"] = np.append(metrics["Draws"], draws)
                        metrics["Losses"] = np.append(metrics["Losses"], losses)
                    else:
                        st.error(f"Failed to retrieve data for {username}. Please check the username.")
                        return

                st.success(f"Metrics for {username} for {selected_game_mode} games fetched successfully!")
                
                st.write(f"**Metrics** for {selected_game_mode} games for _All Time_:")

                idx = np.where(game_modes == selected_game_mode)
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Games Played", int(metrics["Games Played"][idx])) # I used int just to remove the additional .0 decimal point added automatically by this version of Streamlit
                col2.metric("Wins", int(metrics["Wins"][idx]))
                col3.metric("Draws", int(metrics["Draws"][idx]))         
                col4.metric("Losses", int(metrics["Losses"][idx]))

                # handle division by zero
                # resOrNaN = metrics['Games Played'][idx] and col2.metric("Win %", f"{(metrics['Wins'][idx] / metrics['Games Played'][idx] * 100):.2f}%") or col2.metric("Win %", f"NaN")

                # handle division by zero
                if metrics['Games Played'][idx]:
                    # col2.metric("Win %", list(map('{:.1f}%'.format, metrics['Wins'][idx] / metrics['Games Played'][idx] * 100))[0])
                    col2.metric("Win %", f"{round(float(metrics['Wins'][idx] / metrics['Games Played'][idx] * 100), 1)}%") # I used float just to remove the additional brackets added automatically by this version of Streamlit
                    col3.metric("Draw %", f"{round(float(metrics['Draws'][idx] / metrics['Games Played'][idx] * 100), 1)}%")
                    col4.metric("Loss %", f"{round(float(metrics['Losses'][idx] / metrics['Games Played'][idx] * 100), 1)}%")
                else:
                    col2.metric("Win %", value = None) # f"NaN"
                    col3.metric("Draw %", value = None)
                    col4.metric("Loss %", value = None)
                
                st.write(f"**Most Favorite Openings** in {selected_game_mode} mode as white and black _since the beginning of 2023_:")

                most_favorite_openings_df = get_most_favorite_openings(username, game_modes)

                selected_game_mode_opening_df = most_favorite_openings_df[most_favorite_openings_df["Game Mode"] == selected_game_mode]
                selected_game_mode_opening_df = selected_game_mode_opening_df.reset_index(drop=True)

                if not selected_game_mode_opening_df.empty:
                    st.dataframe(selected_game_mode_opening_df.style.applymap(lambda x: "background-color: lightgray" if x == "white" else "background-color: black; color: white" if x=="black" else None))
                else:
                    st.info(f"No openings available in {selected_game_mode} mode")
            else:
                st.warning("Please enter a Lichess username.")


if __name__ == "__main__":
    main()
