import json
from typing import Iterable
import discord

from .models import Champion, Team


def get_json(file_path:str) -> dict:
    """
    Get json data to use his data

    Args:
        file_path (str): file's path

    Returns:
        dict: json's data
    """
    with open(file_path, 'r', encoding='utf8') as json_file:
        return json.load(json_file)


data_dict = get_json("data.json")
colors = data_dict["colors"]
champions_list = [Champion(**champion_dict) for champion_dict in data_dict["champions"]]


def is_valid_stage(stage:str) -> bool:
    """
    To estimate if the given stage is valid

    Args:
        stage (str): stage given

    Returns:
        bool: True if stage is valid, False if not.
    """
    floor, stape = stage.split("-")
    floor, stape = int(floor), int(stape)
    return ((floor > 0) and (floor < 30) and (stape > 0) and (stape < 61))

def format_stage(stage:str) -> str:
    """
    Format stage given to store him in database

    Args:
        stage (str): stage given

    Returns:
        str: stage formated
    """
    floor, stape = stage.split("-")
    return str(int(floor)) + "-" + str(int(stape))

def search_champions(champions:Iterable[Champion]=champions_list, **kwargs) -> list[Champion]:
    """
    Returns one or more champions based on filters.

    Args:
        champions (Iterable[Champion], optional): Master list of champions. Defaults to champions_list.

    Returns:
        list[Champion]: Matching champions.
    """
    def key(champion):
        for k,v in kwargs.items():
            if champion.__getattribute__(k) != v: return False
        return True
    
    return list(filter(key, champions))

def select_champions_message_builder(current_position:int, champions:list[int]):
    text = ""
    i = 0
    for champion in champions:
        if champion is not None: champion_name = search_champions(id=champion)[0].name
        else: champion_name = "..."

        if i == current_position: text += f"- **`{i+1}` {champion_name}**\n"
        else: text += f"- `{i+1}` {champion_name}\n"
        i += 1
    return text

def see_team_message_builder(team:Team, like_value:int, team_likes:int) -> discord.Embed:


    if like_value == 0:
        description = ""
    elif like_value == 1:
        description = "⬆️ You like this team ⬆️\n"
    else:
        description = "⬇️ You dislike this team ⬇️\n"

    i = 1
    for champion_id in team.positions:
        if champion_id:
            champion = search_champions(id=champion_id)[0]
            description += f"\n**{i}.** {champion.name}"
        else:
            description += f"\n**{i}.** ..."
        i += 1

    embed = discord.Embed(description=description, color=discord.Colour.blurple(), title=f"Team #{team.id}")
    embed.set_image(url=data_dict["pictures"]["positions"])
    embed.add_field(name="__Stage__", value=f"`{team.stage}`")
    embed.add_field(name="__Likes__", value=f"`{team_likes}`")

    return embed