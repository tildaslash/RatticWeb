#!/usr/bin/env python
'''
Classes to construct a hiearchy holding infoblocks.
'''

# This file is part of python-keepass and is Copyright (C) 2012 Brett Viren.
# 
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.

def path2list(path):
    '''
    Maybe convert a '/' separated string into a list.
    '''
    if isinstance(path,str): 
        path = path.split('/')
        if path[-1] == '': path.pop() # remove trailing '/'
        return path

    return list(path)           # make copy

class Visitor(object):
    '''
    A class that can visit group/entry hierarchy via hier.visit(). 

    A visitor should be a callable with the signature
        
        visitor(obj) -> (value, bail)
        
    The obj is either the node's group or one of it's entries or None.
    The return values control the descent
        
    If value is ever non-None it is assumed the descent is over
    and this value is returned.

    If bail is ever True, the current node is abandoned in the
    descent.  This can be used to avoid sub trees that are not
    interesting to the visitor.
    '''
    def __call__(self):
        notimplemented

    pass

class Walker(object):
    '''
    A class that can visit the node hierarchy

    Like a visitor, this callable should return a tuple of
    (value,bail). non-None to abort the descent and return that value.
    If bail is True, then drop the current node and move to its next
    sister.
    '''
    def __call__(self,node):
        notimplemented
    pass

class NodeDumper(Walker):
    def __call__(self,node):
        if not node.group:
            print 'Top'
            return
        print '  '*node.level*2,node.group.name(),node.group.groupid,\
            len(node.entries),len(node.nodes)

class FindGroupNode(object):
    '''Return the node holding the group of the given name.  If name
    has any slashes it will be interpreted as a path ending in that
    group'''
    def __init__(self,path):
        self._collected = []
        self.best_match = None
        self.path = path2list(path)
        print 'Finding path',path
        return

    def __call__(self,node):
        if not self.path: 
            print 'Bailing, no path'
            return (None,True)
        if not node.group:
            if self.path[0] == "" or self.path[0] == "None" or self.path[0] is None:
                self.path.pop(0)
            print 'Skipping node with null group.'
            return (None,None)

        top_name = self.path[0]
        obj_name = group.name()

        groupid = node.group.groupid
        print self.path,obj_name,groupid

        from infoblock import GroupInfo

        if top_name != obj_name:
            print top_name,'!=',obj_name
            return (None,True) # bail on the current node

        self.best_match = node

        if len(self.path) == 1: # we have a full match
            if self.stop_on_first:
                return node,True # got it!
            else:                # might have a matching sister
                self._collected.append(node)
                return (None,None)
            pass

        self.path.pop(0)
        return (None,None)  # keep going


class CollectVisitor(Visitor):
    '''
    A callable visitor that will collect the groups and entries into
    flat lists.  After the descent the results are available in the
    .groups and .entries data memebers.
    '''
    def __init__(self):
        self.groups = []
        self.entries = []
        return

    def __call__(self,g_or_e):
        if g_or_e is None: return (None,None)
        from infoblock import GroupInfo
        if isinstance(g_or_e,GroupInfo):
            self.groups.append(g_or_e)
        else:
            self.entries.append(g_or_e)
        return (None,None)
    pass


class PathVisitor(Visitor):
    '''
    A callable visitor to descend via hier.visit() method and
    return the group or the entry matching a given path.

    The path is a list of group names with the last element being
    either a group name or an entry title.  The path can be a list
    object or a string interpreted to be delimited by slashs (think
    UNIX pathspec).

    If stop_on_first is False, the visitor will not abort after the
    first match but will instead keep collecting all matches.  This
    can be used to collect groups or entries that are degenerate in
    their group_name or title, respectively.  After the descent the
    collected values can be retrived from PathVisitor.results()

    This visitor also maintains a best match.  In the event of failure
    (return of None) the .best_match data member will hold the group
    object that was located where the path diverged from what was
    found.  The .path data memeber will retain the remain part of the
    unmatched path.
    '''
    def __init__(self,path,stop_on_first = True):
        self._collected = []
        self.best_match = None
        self.stop_on_first = stop_on_first
        self.path = path2list(path)
        return

    def results(self): 
        'Return a list of the matched groups or entries'
        return self._collected

    def __call__(self,g_or_e):
        if not self.path: return (None,None)

        top_name = self.path[0] or "None"
        obj_name = "None"
        if g_or_e: obj_name = g_or_e.name()

        groupid = None
        if g_or_e: groupid = g_or_e.groupid
        #print self.path,obj_name,groupid

        from infoblock import GroupInfo

        if top_name != obj_name:
            if isinstance(g_or_e,GroupInfo):
                return (None,True) # bail on the current node
            else:
                return (None,None) # keep going

        self.best_match = g_or_e

        if len(self.path) == 1: # we have a full match
            if self.stop_on_first:
                return g_or_e,True # got it!
            else:                  # might have a matching sister
                self._collected.append(g_or_e)
                return (None,None)
            pass

        self.path.pop(0)
        return (None,None)  # keep going


class Node(object):
    '''
    A node in the group hiearchy.  

    This basically associates entries to their group

    Holds:

     * zero or one group - zero implies top of hierarchy
     * zero or more nodes
     * zero or more entries
    '''

    def __init__(self,group=None,entries=None,nodes=None):
        self.group = group
        self.nodes = nodes or list()
        self.entries = entries or list()
        return

    def level(self):
        'Return the level of the group or -1 if have no group'
        if self.group: return self.group.level
        return -1

    def __str__(self):
        return self.pretty()

    def name(self):
        'Return name of group or None if no group'
        if self.group: return self.group.group_name
        return None

    def pretty(self,depth=0):
        'Pretty print this Node and its contents'
        tab = '  '*depth


        me = "%s%s (%d entries) (%d subnodes)\n"%\
            (tab,self.name(),len(self.entries),len(self.nodes))

        children=[]
        for e in self.entries:
            s = "%s%s(%s: %s)\n"%(tab,tab,e.title,e.username)
            children.append(s)
            continue

        for n in self.nodes:
            children.append(n.pretty(depth+1))
            continue

        return me + ''.join(children)

    def node_with_group(self,group):
        'Return the child node holding the given group'
        if self.group == group:
            return self
        for child in self.nodes:
            ret = child.node_with_group(group)
            if ret: return ret
            continue
        return None

    pass


def visit(node,visitor):
    '''
    Depth-first descent into the group/entry hierarchy.
    
    The order of visiting objects is: this node's group,
    recursively calling this function on any child nodes followed
    by this node's entries.
    
    See docstring for hier.Visitor for information on the given visitor. 
    '''
    val,bail = visitor(node.group)
    if val is not None or bail: return val
    
    for n in node.nodes:
        val = visit(n,visitor)
        if val is not None: return val
        continue
    
    for e in node.entries:
        val,bail = visitor(e)
        if val is not None or bail: return val
        continue

    return None

def walk(node,walker):
    '''
    Depth-first descent into the node hierarchy.
    
    See docstring for hier.Walker for information on the given visitor. 
    '''
    value,bail = walker(node)
    if value is not None or bail: return value

    for sn in node.nodes:
        value,bail = walk(sn,walker)
        if value is not None: return value
        continue
    return None    
    

def groupid(top):
    'Return group ID unique to groups in nodes below top'
    
    

def mkdir(top,path):
    '''
    Starting at given top node make nodes and groups to satisfy the
    given path, where needed.  Return the node holding the leaf group.
    '''
    import infoblock

    path = path2list(path)
    pathlen = len(path)
    print 'mkdir',path

    fg = FindGroupNode(path)
    node = walk(top,fg)

    if not node:                # make remaining intermediate folders
        print 'Remaining folders to make:',fg.path
        node = fg.best_match
        pathlen -= len(fg.path)
        for group_name in fg.path:
            # fixme, this should be moved into a new constructor
            new_group = infoblock.GroupInfo()
            new_group.groupid = top.gen_groupid()
            new_group.group_name = group_name
            new_group.imageid = 1
            new_group.level = pathlen
            pathlen += 1
            
            new_node = hier.Node(new_group)
            node.nodes.append(new_node)
            
            node = new_node
            group = new_group
            continue
        pass
    return node
    

    
