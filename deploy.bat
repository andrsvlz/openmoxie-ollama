@echo off

echo Building and pushing 'latest'
docker-compose build
docker-compose push

set /p OPENMOXIE_VERSION=<site\VERSION
echo Building and pushing '%OPENMOXIE_VERSION%'
docker-compose build
docker-compose push