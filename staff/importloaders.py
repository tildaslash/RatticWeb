from lib.keepass import kpdb
from cred.models import Cred, Tag


def keepass(filep, password):
    groups = []
    entries = []
    groupstack = []

    db = kpdb.Database(filep, password)

    _walkkeepass(groups, entries, groupstack, db.hierarchy())

    return {'tags': groups, 'entries': entries}

def _walkkeepass(groups, entries, groupstack, root):
    for n in root.nodes:
      t = n.name()
      groupstack.append(t)
      groups.append(t)
      for e in n.entries:
          entries.append({
              'title': e.title,
              'username': e.username,
              'password': e.password,
              'description': e.notes,
              'tags': list(groupstack)
          })
      _walkkeepass(groups, entries, groupstack, n)
      groupstack.pop()

