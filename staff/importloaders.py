from keepassdb import Database


def keepass(filep, password):
    groups = []
    entries = []
    groupstack = []

    db = Database(filep, password)

    _walkkeepass(groups, entries, groupstack, db.root)

    return {'tags': groups, 'entries': entries}


def _walkkeepass(groups, entries, groupstack, root):
    for n in root.children:
        t = n.title
        groupstack.append(t)
        groups.append(t)
        for e in n.entries:
            if e.title != 'Meta-Info':
                entries.append({
                    'title': e.title,
                    'username': e.username,
                    'password': e.password,
                    'description': e.notes,
                    'tags': list(groupstack)
                })
        _walkkeepass(groups, entries, groupstack, n)
        groupstack.pop()
