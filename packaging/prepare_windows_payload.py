"""Add the independently built helper and license materials to the frozen Windows app."""
from pathlib import Path
import argparse
import shutil

parser=argparse.ArgumentParser()
parser.add_argument('--helper',type=Path,required=True)
parser.add_argument('--python-deps',type=Path,required=True)
parser.add_argument('--nuget',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parent.parent
payload=root/'build-output/windows/Wattpin'
(payload/'sensors').mkdir(exist_ok=True)
shutil.copy2(args.helper/'Wattpin.SensorHost.exe',payload/'sensors/Wattpin.SensorHost.exe')
for filename in ['LICENSE','README.md','THIRD_PARTY_NOTICES.md']:
    shutil.copy2(root/filename,payload/filename)
licenses=payload/'licenses'
licenses.mkdir(exist_ok=True)
for info in args.python_deps.glob('*.dist-info'):
    entries=[p.name for p in info.iterdir() if p.is_dir() and p.name=='licenses' or
             p.is_file() and any(token in p.name.lower() for token in ['license','copying','notice'])]
    for directory in entries:
        path=info/directory
        if path.is_dir():shutil.copytree(path,licenses/info.name/directory,dirs_exist_ok=True)
        elif path.is_file():
            (licenses/info.name).mkdir(exist_ok=True)
            shutil.copy2(path,licenses/info.name/path.name)
for path in (root/'packaging/licenses').glob('*'):
    if path.is_file():shutil.copy2(path,licenses/path.name)
for package in args.nuget.iterdir():
    for version in package.iterdir():
        for path in version.iterdir():
            if path.is_file() and ('license' in path.name.lower() or 'notice' in path.name.lower() or path.suffix=='.nuspec'):
                destination=licenses/'nuget'/package.name/version.name
                destination.mkdir(parents=True,exist_ok=True)
                shutil.copy2(path,destination/path.name)
print('Windows payload includes hardware helper and dependency license materials')
