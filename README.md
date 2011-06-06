# dmanai

## what

dmanai is the main repository for ai contestants in [dmangame][1] If you'd like
for other players to be able to play against your AI, fork this repository and
add your AI to it.

[1]:http://github.com/okayzed/dmangame

## playing against others

To run an AI from another user's repository, supply an AI string in the
following format:

    github_user:path_to_ai_module.py

for example: `python main.py okayzed:okay/goose.py` will download
dmanai/okay/goose.py and its dependencies from github.com/okayzed/dmanai.git
and play GooseAI against the local file ai/killncapture.py.

*Remember* to look at AIs before you run them, as you are running remote code
and it can potentially be dangerous.

The -s or --safe-mode flag will use tav's safelite.py module and attempt to
disable most of the ways the executing code can touch your filesystem. If
that's not enough and you'd like to maintain your machine's security, you may
run games on an app engine instance. By default, using the app engine flag will
run them on http://dmangame-app.appspot.com. Anyone can use this app engine
instance and it's encouraged. See the dmangame repository for more information
on using app engine.

## module loading

If you want your AI to be usable by others via the remote AI schema and you
have multiple files, you'll have to make sure any module dependencies you
import are imported via the 'require\_dependency' function in your main AI
class. It knows whether your AI is being loaded from github or filesystem and
imports the module from the same place.

See dmanai/remote\_dep.py for an example AI with dependencies.

## registering an AI to play in ladder matches.

  * Add "PLAY\_IN\_LADDER" as a class variable to your AI's class.

  * Commit and push the AI to your github repository.

  * Inform appengine that you want to register your AI with `python main.py -r
    username:path_to_ai.py.` (e.g. `python main.py -r basic/killncapture.py` - if
    you run this, you'll get a message explaining how to register an AI
    properly)
