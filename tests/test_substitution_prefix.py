import pytest

from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigSubstitutionException, ConfigWrongTypeException


@pytest.mark.parametrize('initial_value', ['null', '0', '"seed"'])
def test_nested_object_reference_after_earlier_namespace(initial_value):
    config = ConfigFactory.parse_string('configuration.param1 = ' + initial_value + '\n' + '''
        server = {
            serverName = "1234"
            user = "reader"
        }
        databaseRole = ${server}
        databaseRole.databaseName = "XD_"${configuration.persistence.suffix}
        configuration.persistence.suffix = "r1"
        configuration.persistence.connection = ${databaseRole}
        dataExport = {
            ssh = {
                host = ${configuration.persistence.connection.serverName}
            }
        }
    ''')
    assert config.get_string('dataExport.ssh.host') == '1234'
    assert config.get_string('configuration.persistence.connection.databaseName') == 'XD_r1'


@pytest.mark.parametrize('declarations', [
    'a = ${b}\nb = ${c}\nc = { value = 1 }\n',
    'c = { value = 1 }\nb = ${c}\na = ${b}\n',
])
@pytest.mark.parametrize('reference, expected', [
    ('${a.value}', 1),
    ('${?a.value}', 1),
    ('[${a.value}]', [1]),
])
def test_dotted_reference_through_object_aliases(declarations, reference, expected):
    config = ConfigFactory.parse_string(declarations + 'result = ' + reference)
    assert config.get('result') == expected


@pytest.mark.parametrize('source', [
    'a = ${b}\nb = ${c}\nc = { "value.key" = 1 }\nresult = ${a."value.key"}',
    '"a.b" = ${b}\nb = ${c}\nc = { value = 1 }\nresult = ${"a.b".value}',
])
def test_dotted_reference_through_quoted_object_aliases(source):
    assert ConfigFactory.parse_string(source).get_int('result') == 1


@pytest.mark.parametrize('depth', [2, 3, 5])
def test_dotted_reference_through_multiple_object_aliases(depth):
    source = ''.join('a{0} = ${{a{1}}}\n'.format(index, index + 1) for index in range(depth))
    source += 'a{0} = {{ value = 1 }}\nresult = ${{a0.value}}'.format(depth)
    assert ConfigFactory.parse_string(source).get_int('result') == 1


@pytest.mark.parametrize('declarations', ['a = 1\n', 'a = ${b}\nb = ${c}\nc = 1\n'])
@pytest.mark.parametrize('optional', ['', '?'])
def test_dotted_reference_rejects_scalar_prefix(declarations, optional):
    with pytest.raises(ConfigWrongTypeException, match='a has type int rather than dict'):
        ConfigFactory.parse_string(declarations + 'result = ${' + optional + 'a.value}')


@pytest.mark.parametrize('declarations', [
    'a = [{ value = 1 }]\n',
    'a = ${b}\nb = ${c}\nc = [{ value = 1 }]\n',
])
def test_dotted_reference_rejects_list_index(declarations):
    with pytest.raises(ConfigWrongTypeException, match='a has type list rather than dict'):
        ConfigFactory.parse_string(declarations + 'result = ${a.0.value}')


@pytest.mark.parametrize('reference', ['pyhocon_issue304_absent.prefix', 'a.pyhocon_issue304_absent'])
@pytest.mark.parametrize('optional', [False, True])
def test_missing_dotted_reference(reference, optional, monkeypatch):
    monkeypatch.delenv(reference, raising=False)
    source = 'a = {}\nresult = ${' + ('?' if optional else '') + reference + '}'
    if optional:
        assert 'result' not in ConfigFactory.parse_string(source)
    else:
        with pytest.raises(ConfigSubstitutionException, match='Cannot resolve variable'):
            ConfigFactory.parse_string(source)


@pytest.mark.parametrize('reference', ['', 'result = ${a.value}\n'])
def test_dotted_reference_does_not_hide_object_alias_cycle(reference):
    with pytest.raises(ConfigSubstitutionException, match='Check for cycles'):
        ConfigFactory.parse_string('a = ${b}\nb = ${a}\n' + reference)
