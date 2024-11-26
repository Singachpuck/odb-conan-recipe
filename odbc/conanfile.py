import os

from conan import ConanFile
from conan.tools.files import get, copy, rmdir, rm, patch, chdir
from conan.tools.gnu import AutotoolsToolchain, Autotools


class ODBCompilerRecipe(ConanFile):
    name = "odb_compiler"
    version = "2.4.0"

    # Optional metadata
    license = "<Put the package license here>"
    author = "Dmytro Ochkas ochkasdmytro@gmail.com"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of hello package here>"
    topics = ("<Put some tag here>", "<here>", "<and here>")

    # Binary configuration
    # settings = "os", "compiler", "build_type", "arch"
    settings = "os", "arch"
    # options = {"shared": [True, False], "fPIC": [True, False]}
    # default_options = {"shared": True, "fPIC": True}

    # Copy sources to the recipe
    exports_sources = "patches*"

    # def generate(self):
    #     if self.info.settings.os == "Linux":
    #         tc = AutotoolsToolchain(self, namespace="libcutl")
    #         tc.generate()

    #         tc = AutotoolsToolchain(self, namespace="odbc")
    #         tc.generate()

    @property
    def _odb_arch(self):
        return "i686" if self.settings.os == "Windows" else self.settings.arch

    @property
    def _odb_directory_name(self):
        return f"odb-{self.version}-{self._odb_arch}-{str(self.settings.os).lower()}{"-gnu" if self.settings.os == "Linux" else ""}"

    @property
    def _odb_build_path(self):
        return os.path.join(self.build_folder, self._odb_directory_name)

    def build(self):
        # libcutl_path = os.path.join(self.build_folder, "libcutl-1.10.0")
        if self.info.settings.os == "Windows":
            get(self, "https://www.codesynthesis.com/download/odb/2.4/odb-2.4.0-i686-windows.zip")
            
            patch(
                self,
                base_path=self._odb_build_path,
                patch_file="patches/odb_std14.patch"
            )
        elif self.info.settings.os == "Linux":
            if self.info.settings.arch == "x86_64":
                get(self, "https://codesynthesis.com/download/odb/2.4/odb-2.4.0-x86_64-linux-gnu.tar.bz2")
                # get(self, "https://codesynthesis.com/download/libcutl/1.10/libcutl-1.10.0.zip")
                # self.run(f"chmod -R 775 {self.source_folder}/libcutl-1.10.0")
                # self.run(f"chmod -R 775 {self.source_folder}/odb-2.4.0")


                # with chdir(self, "./libcutl-1.10.0"):
                #     autotools = Autotools(self, namespace="libcutl")
                #     autotools.configure("libcutl-1.10.0")
                #     # autotools.configure("odb-2.4.0")
                #     autotools.make()
                
                # with chdir(self, "./odb-2.4.0"):
                #     autotools = Autotools(self, namespace="odbc")
                #     autotools.configure("odb-2.4.0", args=[f"--with-libcutl={libcutl_path}"])
                #     # autotools.configure("odb-2.4.0")
                #     autotools.make()
            else:
                raise ValueError(f"Unsupported architecture {self.settings.arch}")
        else:
            raise ValueError(f"Unsupported os {self.settings.os}")
            
    def package(self):
        # odb compiler
        rmdir(self, os.path.join(self._odb_build_path, "doc"))
        rmdir(self, os.path.join(self._odb_build_path, "man"))
        rm(self, "README", self._odb_build_path)
        copy(self, "*", self._odb_build_path, self.package_folder)
        rmdir(self, self._odb_build_path)

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
