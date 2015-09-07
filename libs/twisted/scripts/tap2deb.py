# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.



import sys, os, string, shutil

from twisted.python import usage

class MyOptions(usage.Options):
    optFlags = [["unsigned", "u"]]
    optParameters = [["tapfile", "t", "twistd.tap"],
                  ["maintainer", "m", "", "The maintainer's name and email in a specific format: "
                   "'John Doe <johndoe@example.com>'"],
                  ["protocol", "p", ""],
                  ["description", "e", ""],
                  ["long_description", "l", ""],
                  ["set-version", "V", "1.0"],
                  ["debfile", "d", None],
                  ["type", "y", "tap", "type of configuration: 'tap', 'xml, 'source' or 'python' for .tac files"]]

    #zsh_altArgDescr = {"foo":"use this description for foo instead"}
    #zsh_multiUse = ["foo", "bar"]
    #zsh_mutuallyExclusive = [("foo", "bar"), ("bar", "baz")]
    zsh_actions = {"type":"(tap xml source python)"}
    #zsh_actionDescr = {"logfile":"log file name", "random":"random seed"}

    def postOptions(self):
        if not self["maintainer"]:
            raise usage.UsageError, "maintainer must be specified."


type_dict = {
'tap': 'file',
'python': 'python',
'source': 'source',
'xml': 'xml',
}

def save_to_file(file, text):
    f = open(file, 'w')
    f.write(text)
    f.close()


def run():

    try:
        config = MyOptions()
        config.parseOptions()
    except usage.error, ue:
        sys.exit("%s: %s" % (sys.argv[0], ue))

    tap_file = config['tapfile']
    base_tap_file = os.path.basename(config['tapfile'])
    protocol = (config['protocol'] or os.path.splitext(base_tap_file)[0])
    deb_file = config['debfile'] or 'twisted-'+protocol
    version = config['set-version']
    maintainer = config['maintainer']
    description = config['description'] or ('A Twisted-based server for %(protocol)s' %
                                            vars())
    long_description = config['long_description'] or 'Automatically created by tap2deb'
    twistd_option = type_dict[config['type']]
    date = string.strip(os.popen('date -R').read())
    directory = deb_file + '-' + version
    python_version = '%s.%s' % sys.version_info[:2]

    if os.path.exists(os.path.join('.build', directory)):
        os.system('rm -rf %s' % os.path.join('.build', directory))
    os.makedirs(os.path.join('.build', directory, 'debian'))

    shutil.copy(tap_file, os.path.join('.build', directory))

    save_to_file(os.path.join('.build', directory, 'debian', 'README.Debian'), 
    '''This package was auto-generated by tap2deb\n''')

    save_to_file(os.path.join('.build', directory, 'debian', 'conffiles'), 
    '''\
/etc/init.d/%(deb_file)s
/etc/default/%(deb_file)s
/etc/%(base_tap_file)s
''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'default'), 
    '''\
pidfile=/var/run/%(deb_file)s.pid
rundir=/var/lib/%(deb_file)s/
file=/etc/%(tap_file)s
logfile=/var/log/%(deb_file)s.log
 ''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'init.d'),
    '''\
#!/bin/sh

PATH=/sbin:/bin:/usr/sbin:/usr/bin

pidfile=/var/run/%(deb_file)s.pid \
rundir=/var/lib/%(deb_file)s/ \
file=/etc/%(tap_file)s \
logfile=/var/log/%(deb_file)s.log

[ -r /etc/default/%(deb_file)s ] && . /etc/default/%(deb_file)s

test -x /usr/bin/twistd || exit 0
test -r $file || exit 0
test -r /usr/share/%(deb_file)s/package-installed || exit 0


case "$1" in
    start)
        echo -n "Starting %(deb_file)s: twistd"
        start-stop-daemon --start --quiet --exec /usr/bin/twistd -- \
                          --pidfile=$pidfile \
                          --rundir=$rundir \
                          --%(twistd_option)s=$file \
                          --logfile=$logfile
        echo "."	
    ;;

    stop)
        echo -n "Stopping %(deb_file)s: twistd"
        start-stop-daemon --stop --quiet  \
            --pidfile $pidfile
        echo "."	
    ;;

    restart)
        $0 stop
        $0 start
    ;;

    force-reload)
        $0 restart
    ;;

    *)
        echo "Usage: /etc/init.d/%(deb_file)s {start|stop|restart|force-reload}" >&2
        exit 1
    ;;
esac

exit 0
''' % vars())

    os.chmod(os.path.join('.build', directory, 'debian', 'init.d'), 0755)

    save_to_file(os.path.join('.build', directory, 'debian', 'postinst'),
    '''\
#!/bin/sh
update-rc.d %(deb_file)s defaults >/dev/null
invoke-rc.d %(deb_file)s start
#DEBHELPER#
''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'prerm'),
    '''\
#!/bin/sh
invoke-rc.d %(deb_file)s stop
#DEBHELPER#
''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'postrm'),
    '''\
#!/bin/sh
if [ "$1" = purge ]; then
        update-rc.d %(deb_file)s remove >/dev/null
fi
''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'changelog'),
    '''\
%(deb_file)s (%(version)s) unstable; urgency=low

  * Created by tap2deb

 -- %(maintainer)s  %(date)s

''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'control'),
    '''\
Source: %(deb_file)s
Section: net
Priority: extra
Maintainer: %(maintainer)s
Build-Depends-Indep: debhelper, python (>= 2.6.5-7)
Standards-Version: 3.8.4
XS-Python-Version: current

Package: %(deb_file)s
Architecture: all
Depends: ${python:Depends}, python-twisted-core
XB-Python-Version: ${python:Versions}
Description: %(description)s
 %(long_description)s
''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'copyright'),
    '''\
This package was auto-debianized by %(maintainer)s on
%(date)s

It was auto-generated by tap2deb

Upstream Author(s): 
Moshe Zadka <moshez@twistedmatrix.com> -- tap2deb author

Copyright:

Insert copyright here.
''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'dirs'),
    '''\
etc/init.d
etc/default
var/lib/%(deb_file)s
usr/share/doc/%(deb_file)s
usr/share/%(deb_file)s
''' % vars())

    save_to_file(os.path.join('.build', directory, 'debian', 'rules'),
    '''\
#!/usr/bin/make -f

export DH_COMPAT=5

build: build-stamp
build-stamp:
	dh_testdir
	touch build-stamp

clean:
	dh_testdir
	dh_testroot
	rm -f build-stamp install-stamp
	dh_clean

install: install-stamp
install-stamp: build-stamp
	dh_testdir
	dh_testroot
	dh_clean -k
	dh_installdirs

	# Add here commands to install the package into debian/tmp.
	cp %(base_tap_file)s debian/tmp/etc/
	cp debian/init.d debian/tmp/etc/init.d/%(deb_file)s
	cp debian/default debian/tmp/etc/default/%(deb_file)s
	cp debian/copyright debian/tmp/usr/share/doc/%(deb_file)s/
	cp debian/README.Debian debian/tmp/usr/share/doc/%(deb_file)s/
	touch debian/tmp/usr/share/%(deb_file)s/package-installed
	touch install-stamp

binary-arch: build install

binary-indep: build install
	dh_testdir
	dh_testroot
	dh_strip
	dh_compress
	dh_installchangelogs
	dh_python2
	dh_fixperms
	dh_installdeb
	dh_gencontrol
	dh_md5sums
	dh_builddeb

source diff:                                                                  
	@echo >&2 'source and diff are obsolete - use dpkg-source -b'; false

binary: binary-indep binary-arch
.PHONY: build clean binary-indep binary-arch binary install
''' % vars())

    os.chmod(os.path.join('.build', directory, 'debian', 'rules'), 0755)

    os.chdir('.build/%(directory)s' % vars())
    os.system('dpkg-buildpackage -rfakeroot'+ ['', ' -uc -us'][config['unsigned']])

if __name__ == '__main__':
    run()

