from keepassdb import Database
from django.utils.encoding import smart_text


def keepass(filep, password):
    groups = []
    entries = []
    groupstack = []

    db = Database(filep, password)

    _walkkeepass(groups, entries, groupstack, db.root)

    return {'tags': groups, 'entries': entries}


def _walkkeepass(groups, entries, groupstack, root):
    for n in root.children:
        t = smart_text(n.title, errors='replace')
        groupstack.append(t)
        groups.append(t)
        for e in n.entries:
            if e.title != 'Meta-Info':
                entries.append({
                    'title': smart_text(e.title, errors='replace'),
                    'username': smart_text(e.username, errors='replace'),
                    'password': smart_text(e.password, errors='replace'),
                    'description': smart_text(e.notes, errors='replace'),
                    'url': smart_text(e.url, errors='replace'),
                    'tags': list(groupstack),
                    'filecontent': e.binary,
                    'filename': smart_text(e.binary_desc, errors='replace'),
                })
        _walkkeepass(groups, entries, groupstack, n)
        groupstack.pop()
