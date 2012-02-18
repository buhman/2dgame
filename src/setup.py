try:
    import script_generating_script
    from distutils.core import setup
    import py2exe, pygame
    from modulefinder import Module
    import glob, fnmatch
    import sys, os, shutil
    import operator
except ImportError, message:
    raise SystemExit, "Unable to load module. %s" % message

origIsSystemDLL = py2exe.build_exe.isSystemDLL
def isSystemDLL(pathname):
    if os.path.basename(pathname).lower() in ("libfreetype-6.dll", "libogg-0.dll"):
            return 0
    return origIsSystemDLL(pathname)
py2exe.build_exe.isSystemDLL = isSystemDLL

class pygame2exe(py2exe.build_exe.py2exe):
    def copy_extensions(self, extensions):

        pygamedir = os.path.split(pygame.base.__file__)[0]
        pygame_default_font = os.path.join(pygamedir, pygame.font.get_default_font())

        extensions.append(Module("pygame.font", pygame_default_font))
        py2exe.build_exe.py2exe.copy_extensions(self, extensions)

class BuildExe(object):
    def __init__(self):
        self.script = "game.py"

        self.project_name = "2dgame"

        self.project_url = "http://code.google.com/p/miblog/"

        self.project_version = self.get_rev()

        self.license = "GPLv3"

        self.author_name = "Stephenson & Buhman"
        self.author_email = "zbuhman@gmail.com"
        self.copyright = "Copyright (c) 2011 Stephenson & Buhman."

        self.project_description = "Don't run out of platforms"

        self.icon_file = 'icon.ico'

        self.extra_datas = []

        self.extra_modules = ["pygame._view"]
        self.exclude_modules = ['__gtkagg',
                                '_tkagg',
                                'bsddb',
                                'curses',
                                'email',
                                'pywin.debugger',
                                'pywin.debugger.dbgcon',
                                'pywin.dialogs',
                                'tcl',
                                'Tkconstants',
                                'Tkinter',
                                'numpy',
                                'multiprocessing',
                                'unittest']

        self.exclude_dll = ['tcl84.dll',
                            'tk84.dll',
                            'libgobject-2.0-0.dll',
                            'libgdk-win32-2.0-0.dll']

        self.extra_scripts = []

        self.zipfile_name = None

        self.dist_dir = 'dist'

    def get_rev(self):
        try:
            svn_file = open(os.path.join('.svn', 'entries'), "r")
        except:
            return "r0"
        svn_lines = svn_file.read().split("\n")
        svn_lines.reverse()
        for index, line in enumerate(svn_lines):
            if "zbuhman@gmail.com" in line:
                try:
                    return "r%d" % int(svn_lines[index + 2])
                except ValueError:
                    pass
        return "r0"

    def opj(self, *args):
        path = os.path.join(*args)
        return os.path.normpath(path)

    def find_data_files(self, srcdir, *wildcards, **kw):
        def walk_helper(arg, dirname, files):
            if '.svn' in dirname:
                return
            names = []
            lst, wildcards = arg
            for wc in wildcards:
                wc_name = self.opj(dirname, wc)
                for f in files:
                    filename = self.opj(dirname, f)

                    if fnmatch.fnmatch(filename, wc_name) and not os.path.isdir(filename):
                        names.append(filename)
            if names:
                lst.append((dirname, names))

        file_list = []
        recursive = kw.get('recursive', True)
        if recursive:
            os.path.walk(srcdir, walk_helper, (file_list, wildcards))
        else:
            walk_helper((file_list, wildcards),
                        srcdir,
                        [os.path.basename(f) for f in glob.glob(self.opj(srcdir, '*'))])
        return file_list

    def run(self):
        if os.path.isdir(self.dist_dir):
            shutil.rmtree(self.dist_dir)

        if self.icon_file == None:
            path = os.path.split(pygame.__file__)[0]
            self.icon_file = os.path.join(path, 'pygame.ico')
        print self.icon_file

        extra_datas = []
        for data in self.extra_datas:
            if os.path.isdir(data):
                extra_datas.extend(self.find_data_files(data, '*'))
            else:
                extra_datas.append(('.', [data]))

        setup(
            cmdclass = {'py2exe': pygame2exe},
            version = self.project_version,
            description = self.project_description,
            name = self.project_name,
            url = self.project_url,
            author = self.author_name,
            author_email = self.author_email,
            license = self.license,

            windows = [{
                'script': self.script,
                'icon_resources': [(0, self.icon_file)],
                'copyright': self.copyright
            }],
            options = {'py2exe': {'optimize': 2, 'bundle_files': 1, 'compressed': True, \
                                  'excludes': self.exclude_modules, 'packages': self.extra_modules, \
                                  'dll_excludes': self.exclude_dll,
                                  'includes': self.extra_scripts} },
            zipfile = self.zipfile_name,
            data_files = extra_datas,
            dist_dir = self.dist_dir
            )

        if os.path.isdir('build'):
            shutil.rmtree('build')
        if os.path.exists(os.path.join('dist', "w9xpopen.exe")):
            os.remove(os.path.join('dist', "w9xpopen.exe"))

if __name__ == '__main__':
    sys.argv.append('py2exe')
    BuildExe().run()
