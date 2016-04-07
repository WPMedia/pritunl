import pritunl

import optparse
import sys
import os
import time
import json

USAGE = """\
Usage: pritunl [command] [options]
Command Help: pritunl [command] --help

Commands:
  start                 Start server
  version               Print the version and exit
  reset-password        Reset administrator password
  reset-version         Reset database version to server version
  reset-ssl-cert        Reset the server ssl certificate
  reconfigure           Reconfigure database connection
  set-mongodb           Set the mongodb uri
  logs                  View server logs"""

def main(default_conf=None):
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = 'start'

    parser = optparse.OptionParser(usage=USAGE)

    if cmd == 'start':
        parser.add_option('-d', '--daemon', action='store_true',
            help='Daemonize process')
        parser.add_option('-p', '--pidfile', type='string',
            help='Path to create pid file')
        parser.add_option('-c', '--conf', type='string',
            help='Path to configuration file')
        parser.add_option('-q', '--quiet', action='store_true',
            help='Suppress logging output')
        parser.add_option('--dart-url', type='string',
            help='Dart pub serve url to redirect static requests')
    elif cmd == 'logs':
        parser.add_option('--archive', action='store_true',
            help='Archive log file')
        parser.add_option('--tail', action='store_true',
            help='Tail log file')
        parser.add_option('--limit', type='int',
            help='Limit log lines')

    (options, args) = parser.parse_args()

    if hasattr(options, 'conf') and options.conf:
        conf_path = options.conf
    else:
        conf_path = default_conf
    pritunl.set_conf_path(conf_path)

    if cmd == 'version':
        print '%s v%s' % (pritunl.__title__, pritunl.__version__)
        sys.exit(0)
    elif cmd == 'reset-version':
        from pritunl import setup
        from pritunl import utils

        setup.setup_db()
        utils.set_db_ver(pritunl.__version__)

        time.sleep(.5)
        print 'Database version reset to %s' % pritunl.__version__

        sys.exit(0)
    elif cmd == 'reset-password':
        from pritunl import setup
        from pritunl import auth

        setup.setup_db()
        username, password = auth.reset_password()

        time.sleep(.5)
        print 'Administrator password successfully reset:\n' + \
            '  username: "%s"\n  password: "%s"' % (username, password)

        sys.exit(0)
    elif cmd == 'reconfigure':
        from pritunl import setup
        from pritunl import settings
        setup.setup_loc()

        settings.conf.mongodb_uri = None
        settings.conf.commit()

        time.sleep(.5)
        print 'Database configuration successfully reset'

        sys.exit(0)
    elif cmd == 'get':
        from pritunl import setup
        from pritunl import settings
        setup.setup_db()

        if len(args) != 2:
            raise ValueError('Invalid arguments')

        split = args[1].split('.')
        key_str = None
        group_str = split[0]
        if len(split) > 1:
            key_str = split[1]

        group = getattr(settings, group_str)
        if key_str:
            val = getattr(group, key_str)
            print '%s.%s = %s' % (group_str, key_str,
                json.dumps(val))

        else:
            for field in group.fields:
                val = getattr(group, field)
                print '%s.%s = %s' % (group_str, field, json.dumps(val))

        sys.exit(0)
    elif cmd == 'set':
        from pritunl import setup
        from pritunl import settings
        setup.setup_db()

        if len(args) != 3:
            raise ValueError('Invalid arguments')

        group_str, key_str = args[1].split('.')

        group = getattr(settings, group_str)
        val_str = args[2]
        val = json.loads(val_str)
        setattr(group, key_str, val)

        settings.commit()

        time.sleep(.5)

        print '%s.%s = %s' % (group_str, key_str,
            json.dumps(getattr(group, key_str)))

        sys.exit(0)
    elif cmd == 'unset':
        from pritunl import setup
        from pritunl import settings
        setup.setup_db()

        if len(args) != 2:
            raise ValueError('Invalid arguments')

        group_str, key_str = args[1].split('.')

        group = getattr(settings, group_str)

        group.unset(key_str)

        settings.commit()

        time.sleep(.5)

        print '%s.%s = %s' % (group_str, key_str,
            json.dumps(getattr(group, key_str)))

        sys.exit(0)
    elif cmd == 'set-mongodb':
        from pritunl import setup
        from pritunl import settings
        setup.setup_loc()

        if len(args) > 1:
            mongodb_uri = args[1]
        else:
            mongodb_uri = None

        settings.conf.mongodb_uri = mongodb_uri
        settings.conf.commit()

        time.sleep(.5)
        print 'Database configuration successfully set'

        sys.exit(0)
    elif cmd == 'reset-ssl-cert':
        from pritunl import setup
        from pritunl import settings
        setup.setup_db()

        settings.app.server_cert = None
        settings.app.server_key = None
        settings.commit()

        time.sleep(.5)
        print 'Server ssl certificate successfully reset'

        sys.exit(0)
    elif cmd == 'logs':
        from pritunl import setup
        from pritunl import logger
        setup.setup_db()

        log_view = logger.LogView()

        if options.archive:
            if len(args) > 1:
                archive_path = args[1]
            else:
                archive_path = './'
            print 'Log archived to: ' + log_view.archive_log(archive_path,
                options.limit)
        elif options.tail:
            for msg in log_view.tail_log_lines():
                print msg
        else:
            print log_view.get_log_lines(options.limit)

        sys.exit(0)
    elif cmd != 'start':
        raise ValueError('Invalid command')

    from pritunl import settings

    settings.local.dart_url = options.dart_url

    if options.quiet:
        settings.local.quiet = True

    if options.daemon:
        pid = os.fork()
        if pid > 0:
            if options.pidfile:
                with open(options.pidfile, 'w') as pid_file:
                    pid_file.write('%s' % pid)
            sys.exit(0)
    elif not options.quiet:
        print '##############################################################'
        print '#                                                            #'
        print '#                      /$$   /$$                         /$$ #'
        print '#                     |__/  | $$                        | $$ #'
        print '#   /$$$$$$   /$$$$$$  /$$ /$$$$$$   /$$   /$$ /$$$$$$$ | $$ #'
        print '#  /$$__  $$ /$$__  $$| $$|_  $$_/  | $$  | $$| $$__  $$| $$ #'
        print '# | $$  \ $$| $$  \__/| $$  | $$    | $$  | $$| $$  \ $$| $$ #'
        print '# | $$  | $$| $$      | $$  | $$ /$$| $$  | $$| $$  | $$| $$ #'
        print '# | $$$$$$$/| $$      | $$  |  $$$$/|  $$$$$$/| $$  | $$| $$ #'
        print '# | $$____/ |__/      |__/   \____/  \______/ |__/  |__/|__/ #'
        print '# | $$                                                       #'
        print '# | $$                                                       #'
        print '# |__/                                                       #'
        print '#                                                            #'
        print '##############################################################'

    pritunl.init_server()

if __name__ == '__main__':
    main()
