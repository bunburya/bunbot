from importlib import find_loader
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
            'join',
            'part',
            'nick'
            }

    def __init__(self, bot, plugin_dir):
        self.bot = bot
        self.plugin_dir = plugin_dir
        # NOTE: See if we actually need an OrderedDict (as opp dict) here
        self.loaded_plugins = OrderedDict()

    def register_hook(self, hook_type, plugin, key, func):
        if not hook_type in self.valid_hooks:
            raise PluginLoaderException('Invalid hook type: {}'.format(hook_type))
        self.bot.add_hook(hook_type, key, func)
        try:
            self.hooks_by_plugin[hook_type][plugin].append(key)
        except KeyError:
            self.hooks_by_plugin[hook_type][plugin] = [key]

    def load_plugin(self, name):
        loader = find_loader(name, self.plugin_dir)
        module = loader.load_module()
        self.loaded_plugins[name] = plugin = module.Plugin(self.bot)
        for hook in plugin.hooks:
            hook_type = hook['type']
            key = hook['key']
            func = hook['func']
            self.register_hook(hook_type, name, key, func)



