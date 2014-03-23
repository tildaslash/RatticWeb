from django.http import HttpResponse
from keepassdb import Database


# Returns a HTTPResponse object with a Keepass database in it
def export_keepass(creds, password):
    db = Database()
    groups = {}

    for c in creds:
        # Create the group if we havent yet
        if c.group.name not in groups.keys():
            groups[c.group.name] = db.create_group(title=c.group.name)

        kpg = groups[c.group.name]

        # Add tags list to the end of the description
        tags = '\n\nTags: '
        for t in c.tags.all():
            tags += '['
            tags += t.name
            tags += '] '
        desc = str(c.description) + tags

        # Create the entry
        kpg.create_entry(
            title=c.title,
            username=c.username,
            password=c.password,
            url=c.url,
            notes=desc,
        )

    # Send the response
    response = HttpResponse(mimetype='application/x-keepass')
    db.save(response, password=password)
    response['Content-Disposition'] = 'attachment; filename=RatticExport.kdb'
    response['Content-Length'] = response.tell()
    return response
