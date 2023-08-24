import sqlite3

from .exceptions import LikeNotFound, TeamNotFound
from .models import Like, Team


class Database(object):
    DB_LOCATION = "./database.sqlite3"

    def __init__(self):
        """Initialize db class variables"""
        self.connection = sqlite3.connect(Database.DB_LOCATION)
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        self.cursor.close()
        if isinstance(exc_value, Exception):
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()
    
    def create_database(self, schema:str):
        with open(schema, "r") as f:
            sql = f.read()
            self.cursor.executescript(sql)

    def get_team_with_stage_and_positions(self, stage:str, positions:tuple[int]) -> Team:
        team = None
        seq = []
        for pos in positions:
            if pos is None: seq.append('IS')
            else: seq.append('=')

        self.cursor.execute(f"SELECT * FROM teams WHERE stage = ? AND position1 {seq[0]} ? AND position2 {seq[1]} ? AND position3 {seq[2]} ? AND position4 {seq[3]} ? AND position5 {seq[4]} ?", (stage, *positions))

        team = self.cursor.fetchone()
        if team is None: raise TeamNotFound(Team(stage=stage, positions=positions))
        return Team(team[0], team[1], team[2], team[2:])

    def team_exists(self, stage:str, positions:tuple[int]) -> bool:
        try: self.get_team_with_stage_and_positions(stage, positions)
        except TeamNotFound: return False
        return True

    def get_team_with_id(self, id:int) -> Team:
        self.cursor.execute("SELECT id, user, stage, position1, position2, position3, position4, position5 FROM teams WHERE id=?", (id,))
        team = self.cursor.fetchone()
        if team is None: raise TeamNotFound(Team(id=id))
        return Team(*team[0:3], team[3:])
    
    def get_teams_with_stage(self, stage:str) -> list[Team]:
        self.cursor.execute("SELECT * FROM teams WHERE stage=?", (stage,))
        results = self.cursor.fetchall()
        return [Team(r[0], r[1], stage, (r[3], r[4], r[5], r[6], r[7])) for r in results]
        

    def insert_team(self, user:int, stage:str, positions:tuple[int]) -> Team:
        team = None
        try:
            self.get_team_with_stage_and_positions(stage, positions)
            return
        except TeamNotFound: pass

        self.cursor.execute("INSERT INTO teams(user, stage, position1, position2, position3, position4, position5) VALUES(?, ?, ?, ?, ?, ?, ?)", (user, stage, *positions))
        team = self.cursor.lastrowid
            
        return Team(team, user, stage, positions)

    def remove_team(self, team:int):
        self.cursor.execute("DELETE FROM teams WHERE id=?", (team,))

    def get_user_likes(self, user:int) -> list[Like]:
        likes = []
        
        self.cursor.execute("SELECT user, team, value FROM likes WHERE user=? AND value!=0", (user,))
        results = self.cursor.fetchall()
        likes = [Like(*like) for like in results]
        return likes
    
    def get_like(self, user:int, team:int) -> Like:
        like = None
        
        self.cursor.execute("SELECT value FROM likes WHERE user=? AND team=?", (user, team))
        r = self.cursor.fetchone()
        if r is None: raise LikeNotFound(Like(user=user, team_id=team))
        like = Like(user, team, r[0])
        return like

    def add_like(self, like:Like):
        try:
            like_ = self.get_like(like.user, like.team_id)
            if like_.value != like.value:
                if like.value == 0: self.cursor.execute("DELETE FROM likes WHERE user=? AND team=?", (like.user, like.team_id))
                else: self.cursor.execute("UPDATE likes SET value=? WHERE user=? AND team=?", (like.value, like.user, like.team_id))
        except LikeNotFound:
            self.cursor.execute("INSERT INTO likes(user, team, value) VALUES(?, ?, ?)", (like.user, like.team_id, like.value))

    def get_team_likes(self, team:int) -> int:
        self.cursor.execute("SELECT value FROM likes WHERE team=?", (team,))
        r = self.cursor.fetchall()
        return sum([x[0] for x in r])