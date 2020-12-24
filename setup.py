print("#################")
print("STARTING SETUP.PY")
print("#################\n\n\n")

print("Importing os, sys...")
from os import getcwd, path, makedirs, walk
import sys

file_path = '//'.join(__file__.split('/')[:-1]) or getcwd()

"""
print("Importing nltk...")
import nltk
print("[+] Done (nltk import)\n")

print("Downloading nltk packages...")
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('punkt')
print("[+] Done (nltk packages)\n")

print("Importing git...")
try:
    from git import Repo
except ImportError as err:
    print("\n\n\n")
    print(err)
    print("\n\nTo solve this import error you must download git from"
            " https://git-scm.com/downloads\n    and ensure it is in"
            " PATH (environment variable)")
    exit(-1)

print("[+] Done (git import)\n")

if(not path.exists(f"{file_path}//Structures//Sockets")):
    print("Cloning from git...")
    Repo.clone_from("https://github.com/saisua/Sockets",f"{file_path}//Structures//Sockets")
    print("[+] Done (git clone)\n")
else:
    print("[?] Sockets has already been downloaded")
    print("Fetching to overwrite with the lastest version...")
    local_repository = Repo(f"{file_path}//Structures//Sockets")
    for remote in local_repository.remotes:
        remote.fetch()
    local_repository.git.reset("--hard")
    print("[+] Done (git fetch)\n")
"""

if(not path.isfile(f"{file_path}//geckodriver")):
    print("Importing platform...")
    import platform
    print("[+] Done (platform import)\n")
    
    print("Importing wget...")
    import wget
    print("[+] Done (wget import)\n")

    
    system = (f"{'linux' if platform.system() == 'Linux' else 'win'}"
                f"{'64' if '64' in platform.machine() else '32'}"
                f"{'.tar.gz' if platform.system() == 'Linux' else '.zip'}")
    print(f"Downloading geckodriver ({system})...")
    wget.download(f"https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-{system}",
                        out=f"{file_path}//geckodriver-{system}")


    if(system.endswith("zip")):
        print("Importing zipfile...")
        import zipfile
        print("[+] Done (zipfile import)\n")

        print(f"Extracting geckodriver-{system}... (not tested)")
        zipfile.ZipFile(f"{file_path}//geckodriver-{system}").extractall()
        print(f"[+] Done (extraction)")
    else:
        print("Importing tarfile...")
        import tarfile
        print("[+] Done (tarfile import)\n")

        print(f"Extracting geckodriver-{system}...")
        tarfile.open(f"{file_path}//geckodriver-{system}").extractall()
        print(f"[+] Done (extraction)")

"""
if(not path.exists(f"{file_path}//Extensions//duckduckgo-privacy-extension")):
    print("Importing requests...")
    from requests import get as GET
    print("[+] Done (requests import)\n")

    print("Downloading extension...")
    response = GET("https://addons.mozilla.org/firefox/downloads/file/3560936/duckduckgo_privacy_essentials-2020.4.30-an+fx.xpi?src=dp-btn-primary")
    if(not response.status_code == 200):
        print("Error when downolading an extension")
        exit(-1)

    makedirs(f"{file_path}//Extensions//duckduckgo-privacy-extension//")
    with open(f"{file_path}//Extensions//duckduckgo-privacy-extension//extension.xpi", "wb") as file:
        file.write(response.content)
    print("[+] Done (extension download)\n")

if(path.isdir(f"{file_path}//Extensions//Scraper-src//")):
    if(not "zipfile" in globals()):
        print("Importing zipfile...")
        import zipfile
        print("[+] Done (zipfile import)\n")

    print("Compiling Scraper firefox extension...")
    with zipfile.ZipFile(f"{file_path}//Extensions//scraper-extension//scraper-extension.xpi", 'w') as file:
        for root, dirs, files in walk(f"{file_path}//Extensions//Scraper-src//"):
            for source in files:
                file.write(f"{root}//{source}", 
                    arcname=f"{root[root.find('Scraper-src//')+len('Scraper-src//')-1:]}/{source}"
                )
    print("[+] Done (Scraper firefox extension)")
"""

print("Testing 'requirements.txt' packages...")
print("\tTesting cython...", end=' ')
import Cython
print("Done")
print("\tTesting selenium...", end=' ')
import selenium
print("Done")
print("[+] Done (package testing)\n")

sys.argv.extend(["build_ext","--inplace"])

print("Importing setuptools...")
from setuptools import setup
print("[+] Done (setuptools import)\n")
print("Importing Cython...")
from Cython.Build import cythonize
print("[+] Done (Cython import)\n")
print("Importing Extension...")
from distutils.extension import Extension
print("[+] Done (Extension import)\n")

print("Compiling the program into Cython...\n\n###")
setup(
    name='Scraper',
    ext_modules=cythonize("Browser.pyx", 
                            language="c++", language_level=3),
    zip_safe=False,
    extra_compile_args=["-O3"]
)
print("###\n\n[+] Done (Compilation)\n")