from os import listdir
from os.path import dirname
from sys import path
from importlib import import_module
from collections import OrderedDict

class PluginLoaderException: pass

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
        self.hooks = {hook_type: [] for hook_type in self.valid_hooks}
        self.hooks_by_plugin = {hook_type: [] for hook_type in self.valid_hooks}
        # NOTE: See if we actually need an OrderedDict (as opp dict) here
        self.loaded_plugins = OrderedDict()
        self.load_plugins_from_dir()
    
    def load_plugins_from_dir(self, plugin_dir=None):
        plugin_dir = plugin_dir or self.plugin_dir
        plugins = listdir(plugin_dir)
        for p in plugins:
            self.load_plugin(p.rstrip('.py'))

    def register_hook(self, hook_type, plugin, key, func):
        # TODO: key-based registration doesn't work so well with things
        # like ping, which have no meaningful key; reconsider.
        if not hook_type in self.valid_hooks:
            raise PluginLoaderException('Invalid hook type: {}'.format(hook_type))
        self.hooks[hook_type][key] = func
        try:
            self.hooks_by_plugin[hook_type][plugin].append(key)
        except KeyError:
            self.hooks_by_plugin[hook_type][plugin] = [key]

    def load_plugin(self, name, plugin_dir=None):
        plugin_dir = plugin_dir or self.plugin_dir
        module = import_module('plugins.pong')  # TODO: fix this to import in general,
                                                # maybe have plugins package instead of plugins dir
        self.loaded_plugins[name] = plugin = module.Plugin(self.bot)
        for hook in plugin.hooks:
            hook_type = hook['type']
            func = hook['func']
            key = hook.get('key')   # key is sometimes optional
            self.register_hook(hook_type, name, key, func)
        print('Loaded plugin {}'.format(name))
    
    def exec_cmd_if_exists(self, cmd, data):
        if cmd in self.hooks['command']:
            return self.hooks['command'][cmd](data)
    
    def exec_privmsg_re_if_exists(self, data):
        for re in self.hooks['privmsg_re']:
            if re.match(data.string):
                return self.hooks['privmsg_re'][re](data)

    def exec_privmsg(self, data):
        for hook in self.hooks['privmsg']:
            hook(data)
    
    def exec_self_join(self, data):
        self.conn.say('Hey all!', data.to)
    
    def exec_other_join(self, data):
        self.conn.say('Welcome!', data.to, to=data.from_nick)
