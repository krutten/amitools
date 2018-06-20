from amitools.vamos.path import AssignManager, VolumeManager
from amitools.vamos.cfgcore import ConfigDict


def setup_am(my_path):
  v = VolumeManager()
  v.add_volume("bla", my_path)
  a = AssignManager(v)
  return a


def path_assign_add_del_test(tmpdir):
  my_path = str(tmpdir)
  a = setup_am(my_path)
  # invalid
  assert not a.add_assign('', 'foo:')
  assert not a.add_assign('foo', '')
  # volume of same name
  assert not a.add_assign('bla', 'foo:')
  assert not a.add_assign('BLA', 'foo:')
  # ok
  assert a.add_assign('foo', 'bla:')
  assert a.is_assign('foo')
  assert a.is_assign('FOO')
  assert a.is_assign('Foo')
  assert a.get_all_assigns() == ['foo']
  # ok
  assert a.add_assign('Baz', 'foo:bla/blup')
  assert a.is_assign('baz')
  assert a.is_assign('BAZ')
  assert a.get_all_assigns() == ['foo', 'Baz']
  # invalid path
  assert not a.add_assign('bar', 'bla')
  # duplicate
  assert not a.add_assign('foo', 'blub:')
  assert not a.add_assign('FOO', 'blub:')
  # del foo
  assert a.del_assign('foo')
  # not found
  assert not a.del_assign('bar')


def path_assign_resolve_test(tmpdir):
  my_path = str(tmpdir)
  a = setup_am(my_path)
  a.add_assign('Foo', 'blA:blub')
  a.add_assign('Baz', 'foo:bla/plop')
  a.add_assign('multi', ['foo:tmp', 'baz:'])
  ar = a.resolve_assigns
  # relative paths
  assert ar('rel/path') == 'rel/path'
  assert ar(':rel/path') == ':rel/path'
  # volume path
  assert ar('Bla:abs/path') == 'Bla:abs/path'
  # single assign
  assert ar('Foo:my/path') == 'blA:blub/my/path'
  assert ar('foo:my/path') == 'blA:blub/my/path'
  # single assign recursive
  assert ar('baz:my/path') == 'blA:blub/bla/plop/my/path'
  # multi assign
  assert ar('multi:my/path') == ['blA:blub/tmp/my/path',
                                 'blA:blub/bla/plop/my/path']
  # invalid assign
  assert ar('what:is/here') is None


def path_assign_config_test(tmpdir):
  my_path = str(tmpdir)
  a = setup_am(my_path)
  cfg = ConfigDict({
      "assigns": ConfigDict({
          "Foo": "blA:blub",
          "Baz": 'foo:bla/plop',
          'multi': ['foo:tmp', 'baz:']
      })
  })
  assert a.parse_config(cfg)
  ar = a.resolve_assigns
  # relative paths
  assert ar('rel/path') == 'rel/path'
  assert ar(':rel/path') == ':rel/path'
  # volume path
  assert ar('Bla:abs/path') == 'Bla:abs/path'
  # single assign
  assert ar('Foo:my/path') == 'blA:blub/my/path'
  assert ar('foo:my/path') == 'blA:blub/my/path'
  # single assign recursive
  assert ar('baz:my/path') == 'blA:blub/bla/plop/my/path'
  # multi assign
  assert ar('multi:my/path') == ['blA:blub/tmp/my/path',
                                 'blA:blub/bla/plop/my/path']
  # invalid assign
  assert ar('what:is/here') is None
