from .models import Like, Team


class CustomException(Exception):
    # Class for exceptions created here
    pass

class TeamException(CustomException):
    # Error related to a Team
    pass
class TeamAlreadyExists(TeamException):
    # A Team that already exists tries to be added
    def __init__(self, team:Team, *args: object):
        self.team = team
        super().__init__(*args)
class TeamNotFound(TeamException):
    # A wanted Team does not exist
    def __init__(self, team:Team, *args: object):
        self.team = team
        super().__init__(*args)

class LikeException(CustomException):
    # Error related to a Like
    pass
class LikeNotFound(LikeException):
    # A wanted like does not exist
    def __init__(self, like:Like, *args: object):
        self.like = like
        super().__init__(*args)