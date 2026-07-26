from pythonforandroid.recipes.libffi import LibffiRecipe as OriginalLibffiRecipe
from pythonforandroid.logger import shprint
import sh
import os

class LibffiRecipe(OriginalLibffiRecipe):
    """Custom libffi recipe that skips autoconf regeneration"""
    
    def build_arch(self, arch):
        # Get the build directory
        build_dir = self.get_build_dir(arch.arch)
        
        # Skip autogen.sh - just use the pre-generated configure
        print(f"Skipping libffi autogen.sh in {build_dir}")
        
        # Configure with necessary flags
        configure_dir = self.get_build_dir(arch.arch)
        shprint(sh.bash, os.path.join(configure_dir, 'configure'),
                '--host={}'.format(arch.toolchain_prefix),
                '--disable-shared',
                '--enable-static',
                '--prefix={}'.format(self.get_install_dir(arch)))
        
        # Make
        shprint(sh.make, '-C', configure_dir)
        
        # Install
        shprint(sh.make, '-C', configure_dir, 'install')

recipe = LibffiRecipe()
