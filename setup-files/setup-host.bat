@ echo off

set BASEDIR=%~dp0..

echo Creating git alias "add-pi"
echo     Add a Raspberry Pi as a git-remote for this repo so that updates can be pushed to it
echo     Usage: git add-pi ^<name^>
echo       where ^<name^> is rpi1, rpi2, or rpi3
git -C "%BASEDIR%" config alias.add-pi "!f() { git remote add \"$1\" ssh://\"$1\":/home/pi/atlantic-signatures; }; f"

echo Creating git alias "remove-pi"
echo     Remove a Raspberry Pi from the git-remote list (only needed to temporarily circumvent certain software's policy against private repos)
echo     Usage: git remove-pi ^<name^>
echo       where ^<name^> is rpi1, rpi2, or rpi3
git -C "%BASEDIR%" config alias.remove-pi "!f() { git remote remove \"$1\"; }; f"

echo Creating git alias "update-pi"
echo     Update the atlantic-signatures repo on a Raspberry Pi by force-pushing committed changes from this repo
echo     Usage: git update-pi ^<name^>
echo       where ^<name^> is rpi1, rpi2, or rpi3
git -C "%BASEDIR%" config alias.update-pi "!f() { git push --force \"$1\" main && ssh \"$1\" git -C /home/pi/atlantic-signatures checkout --force main; }; f"

echo Creating git alias "init-pi"
echo     Initialize the atlantic-signatures repo on a Raspberry Pi, including setup of Python environment (only needed once on a new Pi, or if the atlantic-signatures directory is deleted)
echo     Usage: git init-pi ^<name^>
echo       where ^<name^> is rpi1, rpi2, or rpi3
git -C "%BASEDIR%" config alias.init-pi "!f() { git add-pi \"$1\" && ssh \"$1\" git init -b main /home/pi/atlantic-signatures && ssh \"$1\" git -C /home/pi/atlantic-signatures config receive.denyCurrentBranch ignore && git update-pi \"$1\" && ssh \"$1\" chmod +x /home/pi/atlantic-signatures/setup-files/setup-pi.sh && ssh \"$1\" bash -lc /home/pi/atlantic-signatures/setup-files/setup-pi.sh; }; f"
