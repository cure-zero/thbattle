# -*- coding: utf-8 -*-

# -- stdlib --
import logging

# -- third party --

# -- own --
from client.core import Executive
from utils.stats import stats

# -- code --
log = logging.getLogger('commands')
registered_commands = {}


def command(name, help, cmd=None):
    def decorate(f):
        f.commandname = name
        f.commandhelp = help
        registered_commands[cmd or f.__name__] = f
        return f

    return decorate


def argdesc(*desclist):
    def decorate(f):
        f.argdesc = desclist
        return f

    return decorate


def argtypes(*types):
    def decorate(f):
        f.argtypes = types
        return f

    return decorate


def _format_all_commands():
    return '\n'.join([
        '/%s ' % cmdname + cmd.commandname
        for cmdname, cmd in registered_commands.items()
    ])


def process_command(arglist):
    while True:
        if not arglist:
            prompt = _format_all_commands()
            break

        al = list(arglist)
        cmdname = al.pop(0)
        cmd = registered_commands.get(cmdname)
        if not cmd:
            prompt = _format_all_commands()
            break

        if not al and cmdname == '?':
            prompt = '\n'.join((cmd(None), cmd('?')))
            break

        if len(al) != len(cmd.argtypes):
            prompt = registered_commands['?'](cmdname)
            break

        try:
            al = [argtype(i) for argtype, i in zip(cmd.argtypes, al)]
        except:
            prompt = registered_commands['?'](cmdname)
            break

        prompt = cmd(*al)
        break

    return '|R%s|R\n' % prompt if prompt else None

# -----------------------------------


@command('设置提醒显示级别', 'off     禁用提醒\nbasic   启用基本提醒\nat      启用@提醒\nspeaker 为文文新闻显示提醒\nsound   启用声音提醒\nnosound 禁用声音提醒')
@argtypes(str)
@argdesc('<off||basic||at||speaker||sound||nosound>')
def notify(val):
    from user_settings import UserSettings as us

    if val == 'sound':
        us.sound_notify = True
        return '声音提醒已启用。'

    if val == 'nosound':
        us.sound_notify = False
        return '声音提醒已禁用。'

    from utils.notify import NONE, BASIC, AT, SPEAKER
    try:
        level = {
            'off': NONE, 'basic': BASIC,
            'at': AT, 'speaker': SPEAKER,
        }[val]
    except KeyError:
        return registered_commands['?']('notify')

    us.notify_level = level

    return '提醒级别已变更为%s。' % val


@command('帮助', '查看命令的帮助', cmd='?')
@argtypes(str)
@argdesc('[<命令>]')
def help(cmdname):
    cmd = registered_commands.get(cmdname)
    if not cmd:
        return _format_all_commands()
    else:
        help = [cmd.commandname, cmd.commandhelp]
        help.append('/%s ' % cmdname + ' '.join(cmd.argdesc))
        return '\n'.join(help)


@command('踢出观战玩家', 'uid为观战玩家[]中的数字id')
@argtypes(int)
@argdesc('<uid>')
def kickob(uid):
    stats({'event': 'kick_ob'})
    Executive.kick_observer(uid)

    # reply by server message later
    return ''


@command('观战', '只能在大厅内使用，uid为右侧玩家列表中[]内的数字id')
@argtypes(int)
@argdesc('<uid>')
def ob(uid):
    Executive.observe_user(uid)
    return '已经向[%d]发送了旁观请求，请等待回应……' % uid


@command('调试用', '开发者使用的功能，玩家可以忽略')
@argtypes(str, str)
@argdesc('<key>', '<val>')
def dbgval(key, val):
    from utils.misc import dbgvals
    dbgvals[key] = val
    return 'Done'


@command('屏蔽用户', '屏蔽该用户发言')
@argtypes(str)
@argdesc('<用户名>')
def block(user):
    from user_settings import UserSettings as us
    blocked_users = us.blocked_users
    if user not in blocked_users:
        blocked_users.append(user)


@command('取消屏蔽用户', '恢复被屏蔽的用户')
@argtypes(str)
@argdesc('<用户名>')
def unblock(user):
    from user_settings import UserSettings as us
    blocked_users = us.blocked_users
    if user in blocked_users:
        blocked_users.remove(user)


@command('使用物品', '使用在游戏中的物品（比如选将卡、欧洲卡）')
@argtypes(str)
@argdesc('物品名称')
def use(sku):
    from client.core.executive import Executive
    Executive.use_ingame_item(sku)


@command('使用物品', '使用可以在物品页面使用的物品')
@argtypes(int)
@argdesc('物品ID')
def item_use(id):
    from client.core.executive import Executive
    Executive.item_use(id)


@command('列出背包内的物品', 'RT')
@argtypes()
@argdesc()
def item_backpack():
    from client.core.executive import Executive
    Executive.item_backpack()


@command('列出交易所内的物品', 'RT')
@argtypes()
@argdesc()
def item_exchange():
    from client.core.executive import Executive
    Executive.item_exchange()


@command('抽奖', 'RT')
@argtypes(str)
@argdesc('货币类型', 'jiecao|ppoint')
def item_lottery(currency):
    from client.core.executive import Executive
    Executive.item_lottery(currency)
