import subprocess, os

from conan import ConanFile
from conan.tools.env import Environment
from conan.tools.files import get, patch, copy, replace_in_file, rmdir, rm
from conan.tools.microsoft import MSBuild

def get_vs_installation_path():
    # Path to vswhere.exe
    vswhere_path = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    
    # Run vswhere command to get installationPath property
    result = subprocess.run([vswhere_path, "-latest", "-products", "*", "-requires", "Microsoft.Component.MSBuild", "-property", "installationPath"], capture_output=True, text=True)
    
    # Extract the installation path from the result
    installation_path = result.stdout.strip()
    
    return installation_path

def get_msbuild_home():
    vs_installation_path = get_vs_installation_path()
    return f"{vs_installation_path}\MSBuild\Current\Bin"

class PathBuilder:

    def __init__(self):
        self.full_path = ""

    def reset(self):
        self.full_path = ""
        return self

    def append_path(self, path):
        self.full_path = os.pathsep.join((self.full_path, path))
        return self

    def build(self):
        return self.full_path

# TODO: Add channel and user
# TODO: Adapt to Linux
# TODO: Adapt to Visual Studio 2019
# TODO: Add dynamic/static library support
# TODO: Add configurable toolchain in the patches
# TODO: Adapt to different db types via options
# TODO: Adapt to different versions
# TODO: Add with compiler option
class ODBRecipe(ConanFile):
    name = "odb"
    version = "2.4.0"

    # Optional metadata
    license = "<Put the package license here>"
    author = "Dmytro Ochkas ochkasdmytro@gmail.com"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of hello package here>"
    topics = ("<Put some tag here>", "<here>", "<and here>")

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": True, "fPIC": True}

    # Copy sources to the recipe
    exports_sources = "patches*", "cmake*"

    @property
    def _cmake_install_base_path(self):
        return os.path.join("lib", "cmake", "odb")

    def config_options(self):
        if self.settings.os == "Windows":
            self.options["libpq/15.5"].shared = True
            del self.options.fPIC

    def source(self):
        get(self, "https://www.codesynthesis.com/download/odb/2.4/libodb-2.4.0.zip")
        get(self, "https://www.codesynthesis.com/download/odb/2.4/libodb-pgsql-2.4.0.zip")
        get(self, "https://www.codesynthesis.com/download/odb/2.4/odb-2.4.0-i686-windows.zip")

        libodb_pgsql_path = os.path.join(self.source_folder, "libodb-pgsql-2.4.0")
        libodb_path = os.path.join(self.source_folder, "libodb-2.4.0")
        odb_path = os.path.join(self.source_folder, "odb-2.4.0-i686-windows")
        patch(
            self,
            base_path=libodb_path,
            patch_file="patches/retarget-v143.patch"
        )

        patch(
            self,
            base_path=libodb_pgsql_path,
            patch_file="patches/retarget-pgsql-v143.patch"
        )

        patch(
            self,
            base_path=odb_path,
            patch_file="patches/odb_std14.patch"
        )

    def requirements(self):
        self.requires("libpq/15.5")

    def generate(self):
        ms_build_home = get_msbuild_home()
        # TODO: Write logs instead 
        # print(ms_build_home)

        env = Environment()
        env.append_path("PATH", ms_build_home)
        envvars = env.vars(self, scope="build")
        envvars.save_script("msbuild_env")

    def build(self):
        if self.settings.os == "Windows":
            msbuild = MSBuild(self)
            msbuild.build("libodb-2.4.0/libodb-vc17.sln")

            libpq_path = self.dependencies["libpq"].package_folder
            libodb_path = os.path.join(self.build_folder, "libodb-2.4.0")

            includePath = PathBuilder().reset() \
                .append_path("$(VC_IncludePath)") \
                .append_path("$(WindowsSDK_IncludePath)") \
                .append_path(libodb_path) \
                .append_path(os.path.join(libpq_path, "include")) \
                .build()
            executePath = PathBuilder() \
                .reset() \
                .append_path("$(VC_ExecutablePath_x64)") \
                .append_path("$(CommonExecutablePath)") \
                .append_path(os.path.join(libodb_path, "bin64")) \
                .append_path(os.path.join(libpq_path, "bin")) \
                .build()
            libPath = PathBuilder() \
                .reset() \
                .append_path("$(VC_LibraryPath_x64)") \
                .append_path("$(WindowsSDK_LibraryPath_x64)") \
                .append_path(os.path.join(libodb_path, "lib64")) \
                .append_path(os.path.join(libpq_path, "lib")) \
                .build()

            replace_in_file(self, "libodb-pgsql-2.4.0/odb/pgsql/libodb-pgsql-vc17.vcxproj", "{{includePath}}", includePath)
            replace_in_file(self, "libodb-pgsql-2.4.0/odb/pgsql/libodb-pgsql-vc17.vcxproj", "{{executablePath}}", executePath)
            replace_in_file(self, "libodb-pgsql-2.4.0/odb/pgsql/libodb-pgsql-vc17.vcxproj", "{{libraryPath}}", libPath)

            msbuild.build("libodb-pgsql-2.4.0/libodb-pgsql-vc17.sln")
        else:
            raise ValueError(f"Unsupported os: {self.settings.os}")

    def package(self):
        if self.settings.os == "Windows":
            # libodb
            copy(self, "*.dll", os.path.join(self.build_folder, "libodb-2.4.0", "bin64"), os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", os.path.join(self.build_folder, "libodb-2.4.0", "lib64"), os.path.join(self.package_folder, "lib"))
            copy(self, "*.hxx", os.path.join(self.build_folder, "libodb-2.4.0", "odb"), os.path.join(self.package_folder, "include", "odb"))
            copy(self, "*.ixx", os.path.join(self.build_folder, "libodb-2.4.0", "odb"), os.path.join(self.package_folder, "include", "odb"))
            copy(self, "*.txx", os.path.join(self.build_folder, "libodb-2.4.0", "odb"), os.path.join(self.package_folder, "include", "odb"))
            copy(self, "*.h", os.path.join(self.build_folder, "libodb-2.4.0", "odb"), os.path.join(self.package_folder, "include", "odb"))

            # libodb-pgsql
            copy(self, "*.dll", os.path.join(self.build_folder, "libodb-pgsql-2.4.0", "bin64"), os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", os.path.join(self.build_folder, "libodb-pgsql-2.4.0", "lib64"), os.path.join(self.package_folder, "lib"))
            copy(self, "*.hxx", os.path.join(self.build_folder, "libodb-pgsql-2.4.0", "odb"), os.path.join(self.package_folder, "include", "odb"))
            copy(self, "*.ixx", os.path.join(self.build_folder, "libodb-pgsql-2.4.0", "odb"), os.path.join(self.package_folder, "include", "odb"))
            copy(self, "*.txx", os.path.join(self.build_folder, "libodb-pgsql-2.4.0", "odb"), os.path.join(self.package_folder, "include", "odb"))
            copy(self, "*.h", os.path.join(self.build_folder, "libodb-pgsql-2.4.0", "odb"), os.path.join(self.package_folder, "include", "odb"))

            # odb compiler
            rmdir(self, os.path.join(self.build_folder, "odb-2.4.0-i686-windows", "doc"))
            rmdir(self, os.path.join(self.build_folder, "odb-2.4.0-i686-windows", "man"))
            rm(self, "README", os.path.join(self.build_folder, "odb-2.4.0-i686-windows"))
            copy(self, "odb-2.4.0-i686-windows*", self.build_folder, self.package_folder)
            rmdir(self, os.path.join(self.build_folder, "odb-2.4.0-i686-windows"))

            # cmake modules
            copy(self, "cmake*", self.source_folder, os.path.join(self.package_folder, "lib"))
        else:
            raise ValueError(f"Unsupported os: {self.settings.os}")

    def package_info(self):
        self.cpp_info.libs = ["odb", "odb-pgsql"]
        self.cpp_info.builddirs = [self._cmake_install_base_path]

        build_modules = [
            os.path.join(self._cmake_install_base_path, "OdbTarget.cmake"),
            os.path.join(self._cmake_install_base_path, "GenerateOdb.cmake")
        ]
        self.cpp_info.set_property("cmake_build_modules", build_modules)