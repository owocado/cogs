## Pre-requisites

⚠ NOTE: Installing pre-requisites and all of Manim's dependencies + Docker image may take considerable amount of disk space (roughly from 1GB up to 4GB if TeX packages are also installed) and may consume significant amount of internet bandwidth while trying to download prerequisite software packages.
⚠ NOTE: Docker images are only available for Linux/Unix based OS architectures.

* First install docker for your OS where you are running/hosting your Red instance.
* Install required dependencies for Manim from: https://docs.manim.community/en/stable/installation.html


## Pull Manim docker image

by using this command in your terminal (may require you to run with sudo):
```
docker pull manimcommunity/manim:stable
```
Current Manim stable docker image version as of 3rd October 2021 is v0.11.0

It may take sometime to download+extract this docker image, depending on your ISP host provider's internet speed.
Once it's done, check if its successfully downloaded with:
```
$ docker images -a
REPOSITORY             TAG       IMAGE ID       CREATED        SIZE
manimcommunity/manim   stable    a9ffd7d499c3   15 hours ago   1.89GB
```

# Install manim cog
```
# Add this repo, if haven't already
[p]repo add owo-cogs https://github.com/siu3334/owo-cogs

# Install cog
[p]cog install owo-cogs manim

# Load the cog
[p]load manim
```

If it's loaded successfully, then try evaluating a Manim code snippet with `[p]manimate` command like this:
![image](https://user-images.githubusercontent.com/24418520/114295266-c9cdb780-9ac1-11eb-9d43-64ae427d5c60.png)

Or pick a code snippet from Manim's example gallery to try out for demo: https://docs.manim.community/en/stable/examples.html
