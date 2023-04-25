## Pre-requisites

> **Warning**
> Installing pre-requisites and all of Manim's dependencies + Docker image may take considerable amount of disk space (anywhere from 1 to 4 GiB if TeX packages are also installed) and may consume significant amount of internet bandwidth while trying to download prerequisite software packages.

> **Note**
> Docker images are only available for Linux/Unix based OS architectures.

* First install docker for your OS where you are running/hosting your redbot instance.
* Install required dependencies for Manim from: https://docs.manim.community/en/stable/installation.html


## Pull Manim docker image

by using this command in your terminal (may require you to run with sudo):
```
docker pull manimcommunity/manim:stable
```
Current stable Manim docker image version as of 25th April 2023 is v0.17.3

It may take sometime to download+extract this docker image, depending on your ISP host provider's internet speed.
Once it's done, check if its successfully downloaded with:
```
$ docker images -a
REPOSITORY             TAG       IMAGE ID       CREATED       SIZE
manimcommunity/manim   stable    a594bd60e7a7   2 weeks ago   1.97GB
```

# Install manim cog
```
# Add this repo, if haven't already
[p]repo add owo-cogs https://github.com/owocado/owo-cogs

# Install cog
[p]cog install owo-cogs manim

# Load the cog
[p]load manim
```

If it's loaded successfully, then try evaluating a Manim code snippet with `[p]manimate` command like this:
![image](https://user-images.githubusercontent.com/24418520/114295266-c9cdb780-9ac1-11eb-9d43-64ae427d5c60.png)

Or pick a code snippet from Manim's example gallery to try out for demo: https://docs.manim.community/en/stable/examples.html
