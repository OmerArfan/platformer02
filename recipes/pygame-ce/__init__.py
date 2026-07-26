from os.path import join

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

    def ensure_hostpython_has_cython(self, arch):
        """
        pygame-ce's setup.py hard-requires `import Cython` to succeed in
        whatever interpreter runs it. That interpreter is the isolated
        "hostpython3 native-build" - a standalone CPython built to run
        setup.py scripts on the host machine - which is NOT the same
        Python as the one on the CI/build machine (where we already
        `pip install cython`). Without this, build fails with:
        "You need cython. https://cython.org/, pip install cython --user"
        """
        env = self.get_recipe_env(arch)
        hostpython = sh.Command(self.ctx.hostpython)
        try:
            shprint(hostpython, "-m", "ensurepip", "--upgrade", _env=env)
        except sh.ErrorReturnCode:
            pass  # pip may already be present
        shprint(hostpython, "-m", "pip", "install", "--upgrade", "pip", _env=env)
        shprint(hostpython, "-m", "pip", "install", "cython", _env=env)

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        self.ensure_hostpython_has_cython(arch)
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

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["USE_SDL2"] = "1"
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = Pygame2Recipe()
