import os

import discord
from discord import app_commands

from core import (Database, Like, LikesView, SelectChampionsView, Team,
                  data_dict, exceptions, format_stage, is_valid_stage,
                  search_champions, see_team_message_builder,
                  select_champions_message_builder)

MY_GUILD = discord.Object(id=914554436926447636)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.tree.command(name="create-team", description="Create and share a team for a specific stage")
@app_commands.describe(stage='Stage concerned by this team in the format "[floor][stape]"')
async def create_team(interaction:discord.Interaction, stage:str):
    try:
        if not is_valid_stage(stage):
            return await interaction.response.send_message("This stage is not valid...", ephemeral=True)
        stage = format_stage(stage)
    except:
        return await interaction.response.send_message("This stage is not valid...", ephemeral=True)

    
    view = SelectChampionsView(stage, interaction.user.id)
    embed = discord.Embed(color=discord.Color.blurple(), title=f"Create and share a team for stage `{stage}`", description=select_champions_message_builder(view.current_position, view.positions))
    embed.set_image(url=data_dict["pictures"]["positions"])
    view.embed = embed
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@client.tree.command(name="team", description="See team details")
@app_commands.describe(team_id="Id of team you want details", )
@app_commands.rename(team_id="id", )
async def team_(interaction:discord.Interaction, team_id:int):
    try:
        with Database() as db: team = db.get_team_with_id(team_id)
    except exceptions.TeamNotFound as e:
        return await interaction.response.send_message(f"No team with id `#{e.team.id}` exists...", ephemeral=True)
    
    try:
        with Database() as db:
            like_value = db.get_like(interaction.user.id, team.id).value
    except exceptions.LikeNotFound:
        like_value = 0
    
    with Database()as db:
        team_likes = db.get_team_likes(team.id)

    embed = see_team_message_builder(team, like_value, team_likes)
    view = LikesView(user_id=interaction.user.id, team=team, embed=embed)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@client.tree.command(name="delete-team", description="Delete one of your shared teams")
@app_commands.describe(team='Team you want to delete')
async def delete_team(interaction:discord.Interaction, team:int):
    with Database() as db:
        team:Team = db.get_team_with_id(team)
    if team.user != interaction.user.id:
        await interaction.response.send_message("It's not your team...", ephemeral=True)
    else:
        with Database() as db:
            db.remove_team(team.id)
        await interaction.response.send_message("Deleted !", ephemeral=True)


@client.tree.command(name="stage", description="See best teams for a specific stage")
@app_commands.describe(stage='Stage you want to see teams in the format "[floor][stape]"')
async def stage(interaction:discord.Interaction, stage:str):
    try:
        if not is_valid_stage(stage):
            return await interaction.response.send_message("This stage is not valid...", ephemeral=True)
        stage = format_stage(stage)
    except:
        return await interaction.response.send_message("This stage is not valid...", ephemeral=True)
    
    with Database() as db: teams = db.get_teams_with_stage(stage)
    teams_with_likes = []

    for team in teams:
        with Database() as db: teams_with_likes.append((team, db.get_team_likes(team.id)))
    leaderboard = sorted(teams_with_likes, key=lambda x: x[1], reverse=True)

    text = ""
    rank = 1
    for team, likes in leaderboard:
        text += f"**{rank}.** `#{team.id}` ({likes})\n"
        rank += 1

    await interaction.response.send_message(text, ephemeral=True)



if __name__ == "__main__":
    with Database() as db: db.create_database("database_schema.sql")
    client.run(os.getenv("TOKEN"))