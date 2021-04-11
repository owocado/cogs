## Pre-requisites

⚠ WARNING: Install pre-requisites and all of Manim's dependencies + Docker image may take considerable amount of disk space (roughly 1GB to 4GB if TeX packages are also installed).

* First install docker for your OS where you are running/hosting your Red instance.
* Install required dependencies for Manim from: https://docs.manim.community/en/stable/installation.html


## Pull Manim docker image

by using this command in your terminal:
```
docker pull manimcommunity/manim:stable
```
It may take sometime to download+extract this docker image, depending on your provider's internet speed.
Once it's done, check if its successfully downloaded with:
```
$ docker images
REPOSITORY             TAG       IMAGE ID       CREATED      SIZE
manimcommunity/manim   stable    75bf1808c3a7   9 days ago   1.58GB
```

# Install manim cog
```
# Add this repo, if haven't already
[p]repo add owo-cogs https://github.com/jenkins420/cowogs

# Install cog
[p]cog install owo-cogs manim

# Load the cog
[p]load manim
```

If it's loaded successfully, then try evaluating a Manim code snippet with `[p]manimate` command like this:
![image](https://user-images.githubusercontent.com/24418520/114295266-c9cdb780-9ac1-11eb-9d43-64ae427d5c60.png)

Or pick a code snippet from Manim's example gallery: https://docs.manim.community/en/stable/examples.html
