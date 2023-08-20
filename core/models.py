class Team:
    # Represents a team for a specific stage
    __slots__ = ["id", "user", "stage", "positions"]

    def __init__(self, id:int=None, user:int=None, stage:str=None, positions:tuple[int]=None):
        """
        Args:
            id (int, optional): Team id. Defaults to None.
            user (int, optional): User who created the team. Defaults to None.
            stage (str, optional): Stage concerned by this team. Defaults to None.
            positions (tuple[int], optional): Positions of champions. Defaults to None.
        """
        self.id = id
        self.user = user
        self.stage = stage
        self.positions = positions

class Like:
    #Represents a like
    __slots__ = ["user", "team_id", "value"]

    def __init__(self, user:int=None, team_id:int=None, value:int=None):
        """
        Args:
            user (int, optional): User who liked the team. Defaults to None.
            team_id (int, optional): Id of the liked team. Defaults to None.
            value (int, optional): To know the value of this like, -1 if it's a dislike and 1 if it's a like. Defaults to None.
        """
        self.user = user
        self.team_id = team_id
        self.value = value

class Champion:
    # Represents a champion
    __slots__ = ["id", "name", "rarity", "color"]

    def __init__(self, id:int, name:str, rarity:str, color:str):
        self.id = id
        self.name = name
        self.rarity = rarity
        self.color = color
    