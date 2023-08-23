import discord
from discord.interactions import Interaction

from .database import Database
from .exceptions import LikeNotFound
from .models import Like, Team
from .utils import (colors, search_champions, see_team_message_builder,
                    select_champions_message_builder)


class SelectChampion(discord.ui.Select["SelectChampion"]):
    def __init__(self, color:str):
        champions = search_champions(color=color)
        options = [discord.SelectOption(label=champion.name, value=str(champion.id)) for champion in champions]
        super().__init__(placeholder="Choose champion for this place", options=options)

    async def callback(self, interaction: Interaction):
        view: SelectChampionsView = self.view
        view.select_champion(int(self.values[0]))
        view.reset_items()
        view.embed.description = select_champions_message_builder(view.current_position, view.positions)
        await interaction.response.edit_message(embed=self.view.embed, view=view)

class ColorButton(discord.ui.Button['ColorButton']):
    COLORS = ["yellow", "purple", "blue", "red", "green"]

    def __init__(self, color:str):
        self.color = color
        super().__init__(style=discord.ButtonStyle.blurple, label=colors[color]["name"], emoji=colors[color]["emoji"])

    async def callback(self, interaction:discord.Interaction):
        view: SelectChampionsView = self.view
        view.current_color = self.color
        view.reset_items()
        view.embed.description = select_champions_message_builder(view.current_position, view.positions)
        await interaction.response.edit_message(embed=self.view.embed, view=view)

class PositionButton(discord.ui.Button['PositionButton']):
    def __init__(self, position:int, current_position:int, positions:list[int]):
        self.position = position

        style=None
        if position==current_position:
            if positions[position] is None: style = discord.ButtonStyle.blurple
            else: style = discord.ButtonStyle.green
        else:
            if positions[position] is None: style = discord.ButtonStyle.gray
            else: style = discord.ButtonStyle.green

        super().__init__(style=style, label=str(position+1))

    async def callback(self, interaction:discord.Interaction):
        view: SelectChampionsView = self.view
        view.current_position = self.position
        view.reset_items()
        view.embed.description = select_champions_message_builder(view.current_position, view.positions)
        await interaction.response.edit_message(embed=self.view.embed, view=view)

class ResetButton(discord.ui.Button['ResetButton']):
    def __init__(self):
        style = discord.ButtonStyle.red
        super().__init__(style=style, label="Reset")

    async def callback(self, interaction:discord.Interaction):
        view: SelectChampionsView = self.view
        view.positions = [None, None, None, None, None]
        view.reset_items()
        view.embed.description = select_champions_message_builder(view.current_position, view.positions)
        await interaction.response.edit_message(embed=self.view.embed, view=view)

class ValidateButton(discord.ui.Button['ValidateButton']):
    def __init__(self, positions):
        style = discord.ButtonStyle.green if None not in positions else discord.ButtonStyle.gray
        super().__init__(style=style, label="Validate")

    async def callback(self, interaction:discord.Interaction):
        self.view: SelectChampionsView
        for champion in self.view.positions:
            if champion is not None:
                with Database() as db:
                    if not db.team_exists(self.view.stage, self.view.positions):
                        team:Team = db.insert_team(user=self.view.user, stage=self.view.stage, positions=self.view.positions)
                        await interaction.response.edit_message(embed=None, content=f"Team shared with id `#{team.id}` !", view=None)
                    else:
                        team:Team = db.get_team_with_stage_and_positions(self.view.stage, self.view.positions)
                        with Database() as db: db.add_like(Like(self.view.user, team.id, 1))
                        await interaction.response.edit_message(embed=None, content=f"Team does already exist with id `#{team.id}`, you liked it!", view=None)
                return
        await interaction.response.edit_message(embed=None, content="You need to select 1 champion or more...", view=None)


class SelectChampionsView(discord.ui.View):
    def __init__(self, stage:str, user:int):
        self.stage = stage
        self.user = user
        self.embed = None
        super().__init__(timeout=180)
        self.positions = [None, None, None, None, None]
        self.current_position = 0
        self.current_color = "yellow"
        self.reset_items()

    def reset_items(self):
        self.clear_items()
        self.add_colors_items()
        self.add_select_champion_item()
        self.add_positions_items()
        self.add_reset_and_validate_buttons()
    
    def add_colors_items(self):
        for color in ColorButton.COLORS: self.add_item(ColorButton(color))
    
    def add_select_champion_item(self):
        self.add_item(SelectChampion(self.current_color))

    def add_positions_items(self):
        for i in range(len(self.positions)): self.add_item(PositionButton(i, self.current_position, self.positions))

    def add_reset_and_validate_buttons(self):
        self.add_item(ResetButton())
        self.add_item(ValidateButton(self.positions))

    def select_champion(self, champion:int):
        if champion in self.positions: self.positions[self.positions.index(champion)] = None

        self.positions[self.current_position] = champion
        for i in range(1, len(self.positions)):
            next_position = (self.current_position+i)%5
            if self.positions[next_position] is None:
                self.current_position = next_position
                break

class LikeButton(discord.ui.Button["LikeButton"]):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Like", emoji="⬆️")
    
    async def callback(self, interaction:discord.Interaction):
        self.view: LikesView

        with Database() as db:
            db.add_like(Like(self.view.user_id, self.view.team.id, 1))
        
        await self.view.edit_message(interaction)

class DislikeButton(discord.ui.Button["DislikeButton"]):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Dislike", emoji="⬇️")
    
    async def callback(self, interaction:discord.Interaction):
        self.view: LikesView

        with Database() as db:
            db.add_like(Like(self.view.user_id, self.view.team.id, -1))
        
        await self.view.edit_message(interaction)

class NeutralButton(discord.ui.Button["NeutralButton"]):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Neutral", emoji="➖")
    
    async def callback(self, interaction:discord.Interaction):
        self.view: LikesView

        with Database() as db:
            db.add_like(Like(self.view.user_id, self.view.team.id, 0))
        
        await self.view.edit_message(interaction)

class LikesView(discord.ui.View):
    def __init__(self, user_id:int, team:Team, embed:discord.Embed):
        self.user_id = user_id
        self.team = team
        self.embed = embed
        super().__init__(timeout=180)
        self.add_item(LikeButton())
        self.add_item(NeutralButton())
        self.add_item(DislikeButton())
    
    async def edit_message(self, interaction:discord.Interaction):
        view: LikesView = self

        try:
            with Database() as db:
                like_value = db.get_like(self.user_id, self.team.id).value
        except LikeNotFound:
            like_value = 0
    
            
        with Database()as db:
            team_likes = db.get_team_likes(self.team.id)

        self.embed = see_team_message_builder(self.team, like_value, team_likes)

        await interaction.response.edit_message(embed=self.embed, view=view)
    