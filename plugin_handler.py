from os import listdir
from os.path import dirname, basename
from sys import path
from importlib import import_module
from collections import OrderedDict
import re

class PluginLoaderException: pass

class Hook:

    """Contain information about what functions are called, and when.
    Hooks are stored in plugin scripts as dicts and converted to instances
    of the Hook class by the PluginHandler."""

    def __init__(self, hook_type=None, key=None, func=None, pname=None):
        self.plugin_name = pname
        self.type = hook_type
        self.func = func
        self.key = key

class PluginHandler:

    # Different types of hooks we want to implement:
    # - Command hooks (check first token)
    # - Regex hooks (perform regex on PRIVMSG)
    # - Regex action hooks (perform regex on actions)
    # - Generic privmsg and action hooks (called whenever one is received)
    # - Join, part, kick, ban etc hooks

    valid_hooks = {
            'command',
            'privmsg_re',
            'action_re',
            'privmsg',
            'action',
            'other_join',
            'self_join',
            'part',
            'nick',
            'ping'
            }

    def __init__(self, bot, plugin_dir):
        print('Plugin handler initialising with plugin dir {}'.format(plugin_dir))
        self.bot = bot
        self.conn = bot.conn
        self.plugin_dir = plugin_dir
        self.hooks = {hook_type: {} for hook_type in self.valid_hooks}
        self.hooks_by_plugin = {hook_type: {} for hook_type in self.valid_hooks}
        # NOTE: See if we actually need an OrderedDict (as opp dict) here
        self.loaded_plugins = OrderedDict()
        self.load_plugins_from_dir()
    
    def load_plugins_from_dir(self, plugin_dir=None):
        plugin_dir = plugin_dir or self.plugin_dir
        plugins = filter(lambda fname: fname.endswith('.py'), listdir(plugin_dir))
        for p in plugins:
            self.load_plugin(p.rstrip('.py'))

    def register_hook(self, hook_type, plugin, key, func):
        # TODO: Replace dicts with Hook class.
        # Hooks should contain name of parent plugin, so we can have multiple
        # hooks per key and still be able to remove them properly.
        hook = Hook(hook_type, key, func, plugin)
        if not hook_type in self.valid_hooks:
            raise PluginLoaderException('Invalid hook type: {}'.format(hook_type))
        if key in self.hooks[hook_type]:
            self.hooks[hook_type][key].append(hook)
        else:
            self.hooks[hook_type][key] = [hook]
        try:
            self.hooks_by_plugin[hook_type][plugin].append(key)
        except KeyError:
            self.hooks_by_plugin[hook_type][plugin] = [key]

    def load_plugin(self, name, plugin_dir=None):
        plugin_dir = plugin_dir or self.plugin_dir
        #module = import_module('plugins.rev')  # TODO: fix this to import in general,
                                                # maybe have plugins package instead of plugins dir
        module = import_module('.'.join((basename(plugin_dir), name)))
        self.loaded_plugins[name] = plugin = module.Plugin(self.bot, self)
        for hook in plugin.hooks:
            hook_type = hook['type']
            func = hook['func']
            key = hook.get('key', None)   # key is sometimes optional
            self.register_hook(hook_type, name, key, func)
        print('Loaded plugin {}'.format(name))
    
    def exec_hooks(self, hook_type, key, data):
        for hook in self.hooks.get(hook_type, {}).get(key, []):
            hook.func(data)

    def exec_cmd_if_exists(self, data):
        cmd = data.tokens.pop(0)[1:]
        self.exec_hooks('command', cmd, data)
    
    def exec_privmsg_re_if_exists(self, data):
        for re in self.hooks['privmsg_re']:
            if re.match(data.string):
                return self.hooks['privmsg_re'][re].func(data)

    def exec_privmsg_re_if_exists(self, data):
        for regex in self.hooks['privmsg_re']:
            match = re.search(regex, data.string)
            if match:
                data.regex_match = match
                for hook in self.hooks['privmsg_re'][regex]:
                    hook.func(data)

    def exec_privmsg(self, data):
        for hook in self.hooks['privmsg']:
            hook.func(data)

    # Change these
    
    def exec_self_join(self, data):
        pass
    
    def exec_other_join(self, data):
        pass
