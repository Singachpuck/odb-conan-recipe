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
# TODO: Add with compiler option +
# TODO: Add conandata.yaml
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
    options = {"shared": [True, False], "fPIC": [True, False], "with_compiler": [True, False], "with_pgsql": [True, False]}
    default_options = {"shared": True, "fPIC": True, "with_compiler": True, "with_pgsql": False}

    # Copy sources to the recipe
    exports_sources = "patches*", "cmake*"

    _source_url_base = f"https://www.codesynthesis.com/download/odb/{version[:version.rfind(".")]}"

    @property
    def _libodb_source_dir(self):
        return f"libodb-{self.version}"

    @property
    def _libodb_source_url(self):
        return f"{self._source_url_base}/{self._libodb_source_dir}.zip"

    @property
    def _libodb_pgsql_source_dir(self):
        return f"libodb-pgsql-{self.version}"

    @property
    def _libodb_pgsql_source_url(self):
        return f"{self._source_url_base}/{self._libodb_pgsql_source_dir}.zip"

    _odb_compiler_package_name = "odb_compiler"

    @property
    def _odb_compiler_package(self):
        return f"{self._odb_compiler_package_name}/{self.version}"

    _libpq_package_name = "libpq"
    _libpq_package_version = "15.5"

    @property
    def _libpq_package(self):
        return f"{self._libpq_package_name}/{self._libpq_package_version}"

    @property
    def _cmake_install_base_path(self):
        return os.path.join("lib", "cmake", "odb")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        if self.options.with_pgsql:
            self.options[self._libpq_package].shared = self.options.shared

    def source(self):
        get(self, self._libodb_source_url)
        libodb_path = os.path.join(self.source_folder, self._libodb_source_dir)
        patch(
            self,
            base_path=libodb_path,
            patch_file="patches/retarget-v143.patch"
        )

        get(self, self._libodb_pgsql_source_url)
        libodb_pgsql_path = os.path.join(self.source_folder, self._libodb_pgsql_source_dir)
        patch(
            self,
            base_path=libodb_pgsql_path,
            patch_file="patches/retarget-pgsql-v143.patch"
        )

    def requirements(self):
        if self.options.with_compiler:
            self.requires(self._odb_compiler_package)
        
        if self.options.with_pgsql:
            self.requires(self._libpq_package)

    def generate(self):
        if self.settings.os == "Windows":
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
            msbuild.build(f"{self._libodb_source_dir}/libodb-vc17.sln")
            
            if self.options.with_pgsql:
                libpq_path = self.dependencies[self._libpq_package_name].package_folder
                libodb_path = os.path.join(self.build_folder, self._libodb_source_dir)

                print(libpq_path)
                print(libodb_path)

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

                replace_in_file(self, f"{self._libodb_pgsql_source_dir}/odb/pgsql/libodb-pgsql-vc17.vcxproj", "{{includePath}}", includePath)
                replace_in_file(self, f"{self._libodb_pgsql_source_dir}/odb/pgsql/libodb-pgsql-vc17.vcxproj", "{{executablePath}}", executePath)
                replace_in_file(self, f"{self._libodb_pgsql_source_dir}/odb/pgsql/libodb-pgsql-vc17.vcxproj", "{{libraryPath}}", libPath)

                msbuild.build(f"{self._libodb_pgsql_source_dir}/libodb-pgsql-vc17.sln")
        else:
            raise ValueError(f"Unsupported os: {self.settings.os}")

    def package(self):
        if self.settings.os == "Windows":
            # libodb
            copy(self, "*.dll", os.path.join(self.build_folder, f"{self._libodb_source_dir}", "bin64"), os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", os.path.join(self.build_folder, f"{self._libodb_source_dir}", "lib64"), os.path.join(self.package_folder, "lib"))

            # libodb-pgsql
            if self.options.with_pgsql:
                copy(self, "*.dll", os.path.join(self.build_folder, f"{self._libodb_pgsql_source_dir}", "bin64"), os.path.join(self.package_folder, "bin"))
                copy(self, "*.lib", os.path.join(self.build_folder, f"{self._libodb_pgsql_source_dir}", "lib64"), os.path.join(self.package_folder, "lib"))

            for ext in ["*.hxx", "*.ixx", "*.txx", "*.h"]:
                copy(self, ext, os.path.join(self.build_folder, f"{self._libodb_source_dir}", "odb"), os.path.join(self.package_folder, "include", "odb"))
                if self.options.with_pgsql:
                    copy(self, ext, os.path.join(self.build_folder, f"{self._libodb_pgsql_source_dir}", "odb"), os.path.join(self.package_folder, "include", "odb"))

            # cmake modules
            copy(self, "cmake*", self.source_folder, os.path.join(self.package_folder, "lib"))
            if self.options.with_compiler:
                replace_in_file(self, os.path.join(self.package_folder, self._cmake_install_base_path, "OdbCompilerPath.cmake"),
                    "${__odbc_path__}",
                    self.dependencies[self._odb_compiler_package_name].package_folder.replace("\\", "/"))
        else:
            raise ValueError(f"Unsupported os: {self.settings.os}")

    def package_info(self):
        self.cpp_info.libs = ["odb"]

        if self.options.with_pgsql:
            self.cpp_info.libs.append("odb-pgsql")
            
        self.cpp_info.builddirs = [self._cmake_install_base_path]

        build_modules = []

        if self.options.with_compiler:
            build_modules.append(os.path.join(self._cmake_install_base_path, "OdbCompilerPath.cmake"))
        
        build_modules += [
            os.path.join(self._cmake_install_base_path, "OdbTarget.cmake"),
            os.path.join(self._cmake_install_base_path, "GenerateOdb.cmake")
        ]
        self.cpp_info.set_property("cmake_build_modules", build_modules)
