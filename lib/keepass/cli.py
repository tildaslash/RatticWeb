#!/usr/bin/env python
'''
Command line interface to manipulating keepass files
'''

# This file is part of python-keepass and is Copyright (C) 2012 Brett Viren.
# 
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.

import sys

class Cli(object):
    '''
    Process command line
    '''

    commands = [
        'help',                 # print help message
        'open',                 # open and decrypt a file
        'save',                 # save current DB to file
        'dump',                 # dump current DB to text
        'entry',                # add an entry
        ]

    def __init__(self,args=None):
        self.db = None
        self.hier = None
        self.command_line = None
        self.ops = {}
        if args: self.parse_args(args)
        return

    def parse_args(self,args):
        '''
        keepass.cli [options] [cmd [options]] [...]

        The command line consists of general options followed by zero
        or more commands and their options.

        '''

        def splitopts(argv):
            'Split optional command and its args removing them from input'
            if not argv: return None

            cmd=""
            if argv[0][0] != '-':
                if argv[0] not in Cli.commands:
                    raise ValueError,'Unknown command: "%s"'%argv[0]
                cmd = argv.pop(0)
                pass
            copy = list(argv)
            cmdopts = []
            for arg in copy:
                if arg in Cli.commands: break
                cmdopts.append(argv.pop(0))
                continue
            return [cmd,cmdopts]

        cmdline = []
        copy = list(args)
        while copy:
            chunk = splitopts(copy)
            if not chunk: break

            if not chunk[0]: chunk[0] = 'general'
            meth = eval('self._%s_op'%chunk[0])
            self.ops[chunk[0]] = meth()
            cmdline.append(chunk)
            continue

        self.command_line = cmdline

        return

    def __call__(self):
        'Process commands'
        if not self.command_line:
            print self._general_op().print_help()
            return
        for cmd,cmdopts in self.command_line:
            meth = eval('self._%s'%cmd)
            meth(cmdopts)
            continue
        return

    def _general_op(self):
        '''
        keepassc [options] [cmd cmd_options] ...
        
        Example: open, dump to screen and save

        keepassc open -m "My Secret" input.kpdb \
                 dump -f '"%(title)s" "%(username)s" %(url)s' \
                 save -m "New Secret" output.kpdb

        execute "help" command for more information.
        '''
        from optparse import OptionParser
        op = OptionParser(usage=self._general_op.__doc__)
        return op

    def _general(self,opts):
        'Process general options'
        opts,args = self.ops['general'].parse_args(opts)
        return


    def _help_op(self):
        return None
    def _help(self,opts):
        'Print some helpful information'

        print 'Available commands:'
        for cmd in Cli.commands:
            meth = eval('self._%s'%cmd)
            print '\t%s: %s'%(cmd,meth.__doc__)
            continue
        print '\nPer-command help:\n'

        for cmd in Cli.commands:
            meth = eval('self._%s_op'%cmd)
            op = meth()
            if not op: continue
            print '%s'%cmd.upper()
            op.print_help()
            print
            continue

    def _open_op(self):
        'open [options] filename'
        from optparse import OptionParser
        op = OptionParser(usage=self._open_op.__doc__,add_help_option=False)
        op.add_option('-m','--masterkey',type='string',default="",
                      help='Set master key for decrypting file, default: ""')
        return op

    def _open(self,opts):
        'Read a file to the in-memory database'
        opts,files = self.ops['open'].parse_args(opts)
        import kpdb
        # fixme - add support for openning/merging multiple DBs!
        try:
            dbfile = files[0]
        except IndexError:
            print "No database file specified"
            sys.exit(1)
        self.db = kpdb.Database(files[0],opts.masterkey)
        self.hier = self.db.hierarchy()
        return

    def _save_op(self):
        'save [options] filename'
        from optparse import OptionParser
        op = OptionParser(usage=self._save_op.__doc__,add_help_option=False)
        op.add_option('-m','--masterkey',type='string',default="",
                      help='Set master key for encrypting file, default: ""')
        return op

    def _save(self,opts):
        'Save the current in-memory database to a file'
        opts,files = self.ops['save'].parse_args(opts)
        self.db.update(self.hier)
        self.db.write(files[0],opts.masterkey)
        return

    def _dump_op(self):
        'dump [options] [name|/group/name]'
        from optparse import OptionParser
        op = OptionParser(usage=self._dump_op.__doc__,add_help_option=False)
        op.add_option('-p','--show-passwords',action='store_true',default=False,
                      help='Show passwords as plain text')
        op.add_option('-f','--format',type='string',
                      default='%(group_name)s/%(username)s: %(title)s %(url)s',
                      help='Set the format of the dump')
        return op

    def _dump(self,opts):
        'Print the current database in a formatted way.'
        opts,files = self.ops['dump'].parse_args(opts)
        if not self.hier:
            sys.stderr.write('Can not dump.  No database open.\n')
            return
        print self.hier
        #self.hier.dump(opts.format,opts.show_passwords)
        return
        
    def _entry_op(self):
        'entry [options] username [password]'
        from optparse import OptionParser
        op = OptionParser(usage=self._entry_op.__doc__,add_help_option=False)
        op.add_option('-p','--path',type='string',default='/',
                      help='Set folder path in which to store this entry')
        op.add_option('-t','--title',type='string',default="",
                      help='Set the title for the entry, defaults to username')
        op.add_option('-u','--url',type='string',default="",
                      help='Set a URL for the entry')
        op.add_option('-n','--note',type='string',default="",
                      help='Set a note for the entry')
        op.add_option('-i','--imageid',type='int',default=1,
                      help='Set the image ID number for the entry')
        op.add_option('-a','--append',action='store_true',default=False,
                      help='The entry will be appended instead of overriding matching entry')
        return op

    def _entry(self,opts):
        'Add an entry into the database'
        import getpass
        opts,args = self.ops['entry'].parse_args(opts)
        username = args[0]
        try:
            password = args[1]
        except:
            password1 = password2 = None
            while True:
                password1 = getpass.getpass()
                password2 = getpass.getpass()
                if password1 != password2: 
                    sys.stderr.write("Error: Your passwords didn't match\n")
                    continue
                break
            pass

        self.db.add_entry(opts.path,opts.title or username,username,password,
                          opts.url,opts.note,opts.imageid,opts.append)
        return

if '__main__' == __name__:
    cliobj = Cli(sys.argv[1:])
    cliobj()
