from lib.keepass import kpdb


def keepass(filep, password):
    groups = []
    entries = []
    groupstack = []

    try:
        db = kpdb.Database(filep, password)
    except AttributeError:
        return None

    _walkkeepass(groups, entries, groupstack, db.hierarchy())

    return {'tags': groups, 'entries': entries}

def _walkkeepass(groups, entries, groupstack, root):
    for n in root.nodes:
      groupstack.append(n.name())
      groups.append(n.name())
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

