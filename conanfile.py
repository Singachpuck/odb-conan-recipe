import subprocess

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.env import Environment
from conan.tools.files import get, patch
from conan.tools.microsoft import MSBuild

def get_vs_installation_path():
    # Path to vswhere.exe
    vswhere_path = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\\vswhere.exe"
    
    # Run vswhere command to get installationPath property
    result = subprocess.run([vswhere_path, "-latest", "-products", "*", "-requires", "Microsoft.Component.MSBuild", "-property", "installationPath"], capture_output=True, text=True)
    
    # Extract the installation path from the result
    installation_path = result.stdout.strip()
    
    return installation_path

def get_msbuild_home():
    vs_installation_path = get_vs_installation_path()
    return f"{vs_installation_path}\MSBuild\Current\Bin"

class ODBRecipe(ConanFile):
    name = "odb"
    version = "2.4.0"

    # Optional metadata
    license = "<Put the package license here>"
    author = "<Put your name here> <And your email here>"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of hello package here>"
    topics = ("<Put some tag here>", "<here>", "<and here>")

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    # Sources are located in the same place as this recipe, copy them to the recipe
    exports_sources = "patches*"

    def source(self):
        # Please, be aware that using the head of the branch instead of an immutable tag
        # or commit is a bad practice and not allowed by Conan
        get(self, "https://www.codesynthesis.com/download/odb/2.4/libodb-2.4.0.zip",
                  strip_root=True)

        print(self.source_folder)

        patch(
            self,
            base_path=self.source_folder,
            patch_file="patches/retarget-v143.patch"
        )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    # def layout(self):
    #     cmake_layout(self)

    def generate(self):
        ms_build_home = get_msbuild_home()
        # TODO: Write logs instead 
        print(ms_build_home)

        env = Environment()
        env.append_path("PATH", ms_build_home)
        envvars = env.vars(self, scope="build")
        envvars.save_script("msbuild_env")


        # deps = CMakeDeps(self)
        # deps.generate()
        # tc = CMakeToolchain(self)
        # tc.generate()

    def build(self):
        if self.settings.os == "Windows":
            msbuild = MSBuild(self)
            msbuild.build("libodb-vc12.sln")
        else:
            raise ValueError(f"Unsupported os: {self.settings.os}")

    # def package(self):
    #     cmake = CMake(self)
    #     cmake.install()

    # def package_info(self):
    #     self.cpp_info.libs = ["hello"]