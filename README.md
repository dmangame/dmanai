# dmanai

## what

dmanai is the main repository for ai contestants in [dmangame][1]
This is the main repo for contestants in dmangame
. If you'd like for other players to be
able to play against your AI, fork this repository and add your AI to it.

[1]:http://github.com/okayzed/dmangame

## playing against others

To run an AI from another user's repository, supply an AI string in the
following format:

    github_user:path_to_dep1.py,path_to_dep2.py,path_to_ai_module.py

for example: `python main.py okayzed:okay/okay.py,okay/goose.py
ai/killncapture.py` will download dmanai/okay/okay.py and dmanai/okay/goose.py
from github.com/okayzed/dmanai.git and instantiate an AI instance from the AI
in goose.py to run against the local file ai/killncapture.py.

*Remember* to look at AIs before you run them, as you are running remote code
and it can potentially be dangerous.

If you'd like to maintain your machine's security, you may run games on an app
engine instance. By default, using the app engine flag will run them on
http://dmangame-app.appspot.com. Anyone can use this app engine instance and it's
encouraged. See the dmangame repository for more information on using app engine.

## registering an AI to play in ladder matches.

  * Add "PLAY\_IN\_LADDER" as a class variable to your AI's class.

  * Commit and push the AI to your github repository.

  * Inform appengine that you want to register your AI with `python main.py -r
    username:path_to_ai.py.` (e.g. `python main.py -r basic/killncapture.py` - if
    you run this, you'll get a message explaining how to register an AI
    properly)
