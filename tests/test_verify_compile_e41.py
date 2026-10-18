"""Target-specific read-only proof, with no Docker/Maven invocation."""
from pathlib import Path
import inspect
import pytest
from tools import verify_compile_e41 as v


def test_output_population_is_dynamic_not_t0_count():
    sources=[dict(path='src/main/java/Foo.java'),dict(path='src/test/java/Test.java')]
    classes=dict(classes=[dict(path='a/Foo.class'),dict(path='a/Foo$Inner.class')])
    assert all(v.output_sets_match({'src/main/java/Foo.java'},{'a/Foo.class','a/Foo$Inner.class'},sources,classes).values())
    assert not all(v.output_sets_match({'src/main/java/Foo.java'},{'a/Foo.class'},sources,classes).values())
    assert not all(v.output_sets_match({'src/main/java/Foo.java','src/test/java/Test.java'},{'a/Foo.class','a/Foo$Inner.class'},sources,classes).values())
    assert not all(v.output_sets_match(set(),set(),[],dict(classes=[])).values())


def test_auditor_does_not_execute_or_borrow_t0_expectations():
    source=inspect.getsource(v)
    for forbidden in ('subprocess','.execute_once(','.docker(','.write(','EXPECTED','==37','==106','effective-pom/effective-pom.xml'):
        assert forbidden not in source
    assert 'UNAVAILABLE_NOT_ENUMERATED_BY_REGISTERED_COMPILE' in source
    assert 'UNAVAILABLE_NOT_LOGGED_BY_REGISTERED_COMMAND' in source


@pytest.mark.parametrize('goal',['test','testCompile','manifest','makeAggregateBom','createSPDX','add-module-info','deploy'])
def test_additional_goal_rejected(goal):
    expected=[dict(prefix='compiler',version='3.13.0',goal='compile',execution='default-compile',phase='compile')]
    rows=[dict(expected[0],project='commons-cli'),dict(prefix='bad',version='1',goal=goal,execution='extra',project='commons-cli')]
    assert not v.e.lifecycle_matches(rows,expected)


def test_lifecycle_checks_phase_order_and_identity():
    rows=[dict(prefix='first',version='1',goal='enforce',execution='v',phase='validate'),dict(prefix='compiler',version='3.13.0',goal='compile',execution='default-compile',phase='compile')]
    actual=[dict(r,project='commons-cli') for r in rows]
    assert v.e.lifecycle_matches(actual,rows)
    assert not v.e.lifecycle_matches(actual[::-1],rows)
    actual[0]['project']='unregistered'
    assert not v.e.lifecycle_matches(actual,rows)



def test_synthetic_flags_override_numbered_name_heuristics():
    classes=dict(classes=[dict(path='Foo$1.class',kind='anonymous',access_flags=0x1020),dict(path='Foo$2.class',kind='anonymous',access_flags=0x20),dict(path='Foo$Inner.class',kind='nested',access_flags=0x20)])
    result=v.classify_class_kinds(classes)
    assert [r['kind'] for r in result['classes']]==['synthetic','unnamed_or_local_unresolved','nested']
    assert result['classes'][0]['adapter_kind']=='anonymous'
    assert 'ACC_SYNTHETIC' in result['classes'][0]['classification_basis']



def test_anonymous_class_needs_authoritative_nesting_attributes():
    records=dict(classes=[dict(path='Foo$1.class',kind='anonymous',access_flags=0x20),dict(path='package-info.class',kind='package_info',access_flags=0x1600)])
    metadata={'Foo$1.class':dict(own_inner_record=True,anonymous=True,enclosing_method=True)}
    result=v.classify_class_kinds(records,metadata)
    assert [r['kind'] for r in result['classes']]==['anonymous','package_info']
    assert result['classes'][1]['synthetic_flag']


def test_nesting_parser_rejects_truncated_class():
    with pytest.raises(ValueError):v.nesting_metadata(b'\xca\xfe\xba\xbe')



def test_nesting_parser_reads_real_class_attributes_not_name_suffix():
    import struct
    def utf(s):
        raw=s.encode();return b'\x01'+struct.pack('>H',len(raw))+raw
    pool=utf('p/Foo$1')+b'\x07\x00\x01'+utf('java/lang/Object')+b'\x07\x00\x03'+utf('SourceFile')+utf('Foo.java')+utf('InnerClasses')+utf('EnclosingMethod')
    header=b'\xca\xfe\xba\xbe'+struct.pack('>HHH',0,52,9)+pool
    body=struct.pack('>HHHHHHH',0x20,2,4,0,0,0,3)
    source=struct.pack('>HIH',5,2,6)
    inner=struct.pack('>HIHHHHH',7,10,1,2,0,0,0)
    enclosing=struct.pack('>HIHH',8,4,4,0)
    result=v.nesting_metadata(header+body+source+inner+enclosing)
    assert result==dict(own_inner_record=True,anonymous=True,enclosing_method=True,inner_name=None)
