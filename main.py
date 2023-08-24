import os

import discord
from discord import app_commands

from core import (Database, LikesView, SelectChampionsView, Team,
                  data_dict, exceptions, format_stage, is_valid_stage,
                  see_team_message_builder,
                  select_champions_message_builder)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        self.MY_GUILD = discord.Object(id=str(os.getenv("MY_GUILD")))

        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=self.MY_GUILD)
        await self.tree.sync(guild=self.MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command(name="help", description="See the commands list")
async def help(interaction:discord.Interaction):
    description = "## Commands\n\
                   `help` : show this message\n\
                   `create-team` : create and share a new team\n\
                   `team` : see a team\n\
                   `delete-team` : delete one of your shared teams\n\
                   `stage` : see top 30 of most popular teams for a stage\n\n\
                    ## Useful links\n\
                    > [Discord ToS](https://discord.com/terms)\n\
                    > [Bot ToS](https://github.com/voXrey/RegularTeamMaker)\n\
                    > [Bot Privacy Policy](https://github.com/voXrey/RegularTeamMaker)\n\
                    > [Support server](https://discord.gg/BqJYGtxRbA)\n"

    embed = discord.Embed(title="Help page", description=description, color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed, ephemeral=True)


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
    if len(teams) == 0: return await interaction.response.send_message("There is no team for this stage...", ephemeral=True)
    teams = teams[:30]

    teams_with_likes = []

    for team in teams:
        with Database() as db: teams_with_likes.append((team, db.get_team_likes(team.id)))
    leaderboard = sorted(teams_with_likes, key=lambda x: x[1], reverse=True)

    text = ""
    rank = 1
    for team, likes in leaderboard:
        text += f"**{rank}.** Team `#{team.id}` ➜ {likes} "
        if likes > 0: text += "🔺"
        elif likes < 0: text += "🔻"
        else: text += "🔸"
        text += "\n"

        rank += 1

    embed = discord.Embed(title=f"Top stage {stage} teams", description=text, color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed, ephemeral=True)



if __name__ == "__main__":
    with Database() as db: db.create_database("database_schema.sql")
    client.run(os.getenv("TOKEN"))