from os.path import join
import os

import sh

from pythonforandroid.logger import shprint
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.toolchain import current_directory


class Pygame2Recipe(CythonRecipe):
    """
    Recipe to build apps based on SDL2-based pygame (pygame-ce fork).

    .. warning:: Some pygame functionality is still untested, and some
        dependencies like freetype, postmidi and libjpeg are currently
        not part of the build. It's usable, but not complete.
    """

    version = "2.5.7"
    url = "https://github.com/pygame-community/pygame-ce/archive/refs/tags/{version}.tar.gz"

    site_packages_name = "pygame-ce"
    name = "pygame-ce"

    depends = [
        "sdl2",
        "sdl2_image",
        "sdl2_mixer",
        "sdl2_ttf",
        "setuptools",
        "jpeg",
        "png",
    ]
    call_hostpython_via_targetpython = False  # Due to setuptools
    install_in_hostpython = False

    def ensure_hostpython_has_build_deps(self, arch):
        """
        pygame-ce's setup.py hard-requires `import Cython` to succeed in
        whatever interpreter runs it. That interpreter is the isolated
        "hostpython3 native-build" - a standalone CPython built to run
        setup.py scripts on the host machine - which is NOT the same
        Python as the one on the CI/build machine (where we already
        `pip install cython`). Without this, build fails with:
        "You need cython. https://cython.org/, pip install cython --user"

        We also reinstall setuptools here. The copy already present in
        this hostpython has broken/incomplete vendoring (missing
        more_itertools etc). `pip uninstall` + plain `pip install` wasn't
        enough: it left an empty leftover setuptools/ directory (files
        not tracked by pip's own RECORD, likely baked in by hostpython's
        own build), which Python then imports as an empty PEP 420
        namespace package - "ImportError: cannot import name 'setup'
        from 'setuptools' (unknown location)". `--force-reinstall`
        alone doesn't fix this either: it overwrites tracked files but
        doesn't remove *untracked* leftovers, and a plain `pip install`
        can see the stale directory as "already satisfied" and skip
        writing anything. So we directly rmtree the directories in
        site-packages first, removing any doubt, then do a real install.

        NOTE: we deliberately do NOT run `pip install --upgrade pip` here.
        This hostpython's bundled pip has a broken vendored resolvelib
        (ImportError: cannot import name 'RequirementInformation'), and
        upgrading pip goes through that same broken import path and
        crashes before it can even upgrade itself. --use-deprecated=
        legacy-resolver sidesteps resolvelib entirely for the installs
        below.
        """
        env = self.get_recipe_env(arch)
        hostpython = sh.Command(self.ctx.hostpython)
        try:
            shprint(hostpython, "-m", "ensurepip", "--upgrade", _env=env)
        except sh.ErrorReturnCode:
            pass  # pip may already be present

        # Find the actual site-packages dir this hostpython uses, then
        # forcibly remove any setuptools/pkg_resources remnants directly -
        # don't trust pip's uninstall bookkeeping to catch untracked files.
        site_packages = str(
            hostpython(
                "-c",
                "import sysconfig; print(sysconfig.get_paths()['purelib'])",
                _env=env,
            )
        ).strip()

        import glob
        import shutil

        for pattern in (
            "setuptools",
            "setuptools-*",
            "pkg_resources",
            "pkg_resources-*",
        ):
            for path in glob.glob(join(site_packages, pattern)):
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    try:
                        os.remove(path)
                    except OSError:
                        pass

        shprint(
            hostpython,
            "-m", "pip", "install",
            "--use-deprecated=legacy-resolver",
            "--no-cache-dir",
            "--force-reinstall",
            "setuptools",
            _env=env,
        )
        shprint(
            hostpython,
            "-m", "pip", "install",
            "--use-deprecated=legacy-resolver",
            "cython",
            _env=env,
        )

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            setup_template = open(join("buildconfig", "Setup.Android.SDL2.in")).read()
            env = self.get_recipe_env(arch)
            env["ANDROID_ROOT"] = join(self.ctx.ndk.sysroot, "usr")

            png = self.get_recipe("png", self.ctx)
            png_lib_dir = join(png.get_build_dir(arch.arch), ".libs")
            png_inc_dir = png.get_build_dir(arch)

            jpeg = self.get_recipe("jpeg", self.ctx)
            jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch)

            sdl_mixer_includes = ""
            sdl2_mixer_recipe = self.get_recipe("sdl2_mixer", self.ctx)
            for include_dir in sdl2_mixer_recipe.get_include_dirs(arch):
                sdl_mixer_includes += f"-I{include_dir} "

            setup_file = setup_template.format(
                sdl_includes=(
                    " -I"
                    + join(self.ctx.bootstrap.build_dir, "jni", "SDL", "include")
                    + " -L"
                    + join(self.ctx.bootstrap.build_dir, "libs", str(arch))
                    + " -L"
                    + png_lib_dir
                    + " -L"
                    + jpeg_lib_dir
                    + " -L"
                    + arch.ndk_lib_dir_versioned
                ),
                sdl_ttf_includes="-I"
                + join(self.ctx.bootstrap.build_dir, "jni", "SDL2_ttf"),
                sdl_image_includes="-I"
                + join(self.ctx.bootstrap.build_dir, "jni", "SDL2_image", "include"),
                sdl_mixer_includes=sdl_mixer_includes,
                jpeg_includes="-I" + jpeg_inc_dir,
                png_includes="-I" + png_inc_dir,
                freetype_includes="",
            )
            open("Setup", "w").write(setup_file)

    def build_arch(self, arch):
        # Must run here, NOT in prebuild_arch: prebuild_arch fires during
        # p4a's early prebuild phase, before hostpython3 itself has been
        # compiled and written to disk, so self.ctx.hostpython doesn't
        # exist as a file yet at that point (sh.CommandNotFound).
        # By build_arch time, all dependencies (including hostpython3)
        # are actually built and present.
        self.ensure_hostpython_has_build_deps(arch)
        super().build_arch(arch)

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["USE_SDL2"] = "1"
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = Pygame2Recipe()
