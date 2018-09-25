
class GroupContainsMembers(Exception):
    def __str__(self):
        return("Cannot delete a group that has members.")

class UserNotAuthorized(Exception):
    def __str__(self):
        return("The user did not have permission to do that.")

class UserNotLoggedIn(Exception):
    def __str__(self):
        return("The user is not logged in.")