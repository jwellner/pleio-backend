import enum

class ORDER_DIRECTION(enum.Enum):
    asc = 'asc'
    desc = 'desc'

class ORDER_BY(enum.Enum):
    timeCreated = 'timeCreated'
    timeUpdated = 'timeUpdated'
    lastAction = 'lastAction'

class PLUGIN(enum.Enum):
    events = 'events'
    blog = 'blog'
    discussion = 'discussion'
    question = 'question'
    files = 'files'
    wiki = 'wiki'
    tasks = 'tasks'

class MEMBERSHIP(enum.Enum):
    not_joined = 'not_joined'
    requested = 'requested'
    invited = 'invited'
    joined = 'joined'

class ROLE(enum.Enum):
    owner = 'owner'
    admin = 'admin'
    member = 'member'
    removed = 'removed'
