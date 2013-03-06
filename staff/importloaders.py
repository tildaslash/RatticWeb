from lib.keepass import kpdb


def keepass(filep, password):
    groups = []
    entries = []

    try:
        db = kpdb.Database(filep, password)
    except AttributeError:
        return None

    return {'groups': groups, 'entries': entries}

