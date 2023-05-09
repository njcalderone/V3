#!/usr/bin/python3

"""This script does a version comparison between the versions of packages
from the update under test and the installed versions of the same-named
packages, for whichever packages from the update are installed. It expects
input data that's generated in advisory_check_nonmatching_packages and
advisory_get_installed_packages; you can run it manually against
updatepkgs.txt and installedupdatepkgs.txt logs from a completed test run
if you need to test it or something."""

# no, pylint, global scope variable names in a script like this aren't
# really "constants"
# pylint:disable=invalid-name

import json
import sys
from urllib.request import urlopen

import rpm  # pylint:disable=import-error

def printver(pname, pepoch, pversion, prelease):
    """Print a NEVR in the typical human-readable format."""
    return f"{pname}-{pepoch}:{pversion}-{prelease}"

try:
    updfname = sys.argv[1]
    instfname = sys.argv[2]
except IndexError:
    sys.exit("Must specify two input filenames!")
try:
    updalias = sys.argv[3]
except IndexError:
    updalias = None


updpkgs = {}
with open(updfname, "r", encoding="utf-8") as ufh:
    for uline in ufh.readlines():
        (_, name, epoch, version, release) = uline.strip().split(" ")
        updpkgs[name] = (epoch, version, release)

problems = []
warnings = []
post = set()
ret = 0
updstableobs = None
with open(instfname, "r", encoding="utf-8") as ifh:
    for iline in ifh.readlines():
        (_, name, epoch, version, release) = iline.strip().split(" ")
        res = rpm.labelCompare((epoch, version, release), (updpkgs[name]))
        if res == 0:
            continue
        instver = printver(name, epoch, version, release)
        updver = printver(name, *updpkgs[name])
        if res < 0:
            problems.append(f"Installed: {instver} is older than update: {updver}.")
            post.add("Installed older than update usually means there is a dependency problem preventing the update version being installed.")
            post.add("Check /var/log/dnf.log, and search for the string 'Problem'.")
        else:
            msg = f"Installed: {instver} is newer than update: {updver}"
            if not updalias:
                problems.append(f"{msg} and this is not an update test, please check if this is a problem")
                continue
            # check if the update is stable
            if updstableobs is None:
                try:
                    url = f"https://bodhi.fedoraproject.org/updates/{updalias}"
                    resp = json.loads(urlopen(url).read().decode("utf8"))   # pylint:disable=consider-using-with
                    updstableobs = (resp.get("update", {}).get("status", "") in ("stable", "obsolete"))
                except: # pylint:disable=bare-except
                    problems.append(f"{msg} and Bodhi is unreachable.")
                    continue
            if updstableobs:
                warnings.append(f"{msg} and update is stable or obsolete, this is probably OK.")
            else:
                problems.append(f"{msg} and update is not stable or obsolete.")
                post.add("Installed newer than update and update not stable or obsolete means older version could be pushed over newer if update goes stable.")

if warnings:
    print("WARNINGS")
    for warning in warnings:
        print(warning)
    ret = 2

if problems:
    print("PROBLEMS")
    for problem in problems:
        print(problem)
    ret = 3

if post:
    print("INVESTIGATION TIPS")
    for postmsg in post:
        print(postmsg)

sys.exit(ret)
