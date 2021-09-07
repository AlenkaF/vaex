import numpy as np
import pyarrow as pa
import pytest
from typing import Any, Optional, Tuple, Dict, Iterable, Sequence

DataFrameObject = Any
ColumnObject = Any

import vaex
from common import *
from vaex.dataframe_protocol import _from_dataframe_to_vaex, _DtypeKind, _VaexBuffer, _VaexColumn, _VaexDataFrame


def test_float_only(df_factory):
	df = df_factory(x=[1.5, 2.5, 3.5], y=[9.2, 10.5, 11.8])
	df2 = _from_dataframe_to_vaex(df.__dataframe__())

	assert  df2.x.tolist() == df.x.tolist()
	assert  df2.y.tolist() == df.y.tolist()
	assert df2.__dataframe__().get_column_by_name('x').null_count == 0
	assert df2.__dataframe__().get_column_by_name('y').null_count == 0

	assert_dataframe_equal(df.__dataframe__(), df)

def test_mixed_intfloat(df_factory):
	df = df_factory(x=[1, 2, 0], y=[9.2, 10.5, 11.8])
	df2 = _from_dataframe_to_vaex(df.__dataframe__())

	assert  df2.x.tolist() == df.x.tolist()
	assert  df2.y.tolist() == df.y.tolist()
	assert df2.__dataframe__().get_column_by_name('x').null_count == 0
	assert df2.__dataframe__().get_column_by_name('y').null_count == 0

	assert_dataframe_equal(df.__dataframe__(), df)
	
def test_mixed_intfloatbool(df_factory):
	df = df_factory(
		x=np.array([True, True, False]),
		y=np.array([1, 2, 0]),
		z=np.array([9.2, 10.5, 11.8]))
	df2 = _from_dataframe_to_vaex(df.__dataframe__())

	assert  df2.x.tolist() == df.x.tolist()
	assert  df2.y.tolist() == df.y.tolist()
	assert  df2.z.tolist() == df.z.tolist()
	assert df2.__dataframe__().get_column_by_name('x').null_count == 0
	assert df2.__dataframe__().get_column_by_name('y').null_count == 0
	assert df2.__dataframe__().get_column_by_name('z').null_count == 0

	# Additionl tests for _VaexColumn
	assert df2.__dataframe__().get_column_by_name('x')._allow_copy == True
	assert df2.__dataframe__().get_column_by_name('x').size == 3
	assert df2.__dataframe__().get_column_by_name('x').offset == 0

	assert df2.__dataframe__().get_column_by_name('z').dtype[0]==2 # 2: float64
	assert df2.__dataframe__().get_column_by_name('z').dtype[1] == 64 # 64: float64
	assert df2.__dataframe__().get_column_by_name('z').dtype == (2, 64, '<f8', '=')

	with pytest.raises(TypeError):
	    assert df2.__dataframe__().get_column_by_name('y').describe_categorical
	assert df2.__dataframe__().get_column_by_name('y').describe_null == (3, 1)

	assert_dataframe_equal(df.__dataframe__(), df)

def test_mixed_missing(df_factory_arrow):
	df = df_factory_arrow(
		x=np.array([True, None, False, None, True]),
		y=np.array([None, 2, 0, 1, 2]),
		z=np.array([9.2, 10.5, None, 11.8, None]))

	df2 = _from_dataframe_to_vaex(df.__dataframe__())

	assert df.__dataframe__().metadata == df2.__dataframe__().metadata

	assert df['x'].tolist() == df2['x'].tolist()
	assert not df2['x'].is_masked
	assert df2.__dataframe__().get_column_by_name('x').null_count == 2
	assert df['x'].dtype == df2['x'].dtype

	assert df['y'].tolist() == df2['y'].tolist()
	assert not df2['y'].is_masked
	assert df2.__dataframe__().get_column_by_name('y').null_count == 1
	assert df['y'].dtype == df2['y'].dtype

	assert df['z'].tolist() == df2['z'].tolist()
	assert not df2['z'].is_masked
	assert df2.__dataframe__().get_column_by_name('z').null_count == 2
	assert df['z'].dtype == df2['z'].dtype

	assert_dataframe_equal(df.__dataframe__(), df)

def test_missing_from_masked(df_factory_numpy):
	df = df_factory_numpy(
		x=np.ma.array([1, 2, 3, 4, 0], mask=[0, 0, 0, 1, 1], dtype=int),
		y=np.ma.array([1.5, 2.5, 3.5, 4.5, 0], mask=[False, True, True, True, False], dtype=float),
		z=np.ma.array([True, False, True, True, True], mask=[1, 0, 0, 1, 0], dtype=bool))
	
	df2 = _from_dataframe_to_vaex(df.__dataframe__())

	assert df.__dataframe__().metadata == df2.__dataframe__().metadata

	assert df['x'].tolist() == df2['x'].tolist()
	assert not df2['x'].is_masked
	assert df2.__dataframe__().get_column_by_name('x').null_count == 2
	assert df['x'].dtype == df2['x'].dtype

	assert df['y'].tolist() == df2['y'].tolist()
	assert not df2['y'].is_masked
	assert df2.__dataframe__().get_column_by_name('y').null_count == 3
	assert df['y'].dtype == df2['y'].dtype

	assert df['z'].tolist() == df2['z'].tolist()
	assert not df2['z'].is_masked
	assert df2.__dataframe__().get_column_by_name('z').null_count == 2
	assert df['z'].dtype == df2['z'].dtype

	assert_dataframe_equal(df.__dataframe__(), df)

def test_categorical_ordinal():
	colors = ['red', 'blue', 'green', 'blue']
	ds = vaex.from_arrays(
		colors=colors, 
		year=[2012, 2013, 2015, 2019], 
		weekday=[0, 1, 4, 6])
	df = ds.ordinal_encode('colors', ['red', 'green', 'blue'])
	df = df.categorize('year', min_value=2012, max_value=2019)
	df = df.categorize('weekday', labels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])

	# Some detailed testing for correctness of dtype and null handling:
	col = df.__dataframe__().get_column_by_name('colors')
	assert col.dtype[0] == _DtypeKind.CATEGORICAL
	assert col.describe_categorical == (False, True, {0: 'red', 1: 'green', 2: 'blue'})
	assert col.describe_null == (3, 1)
	assert col.dtype == (23, 64, 'u', '=')
	col2 = df.__dataframe__().get_column_by_name('year')
	assert col2.dtype[0] == _DtypeKind.CATEGORICAL
	assert col2.describe_categorical == (False, True, {0: 2012, 1: 2013, 2: 2014, 3: 2015, 4: 2016, 5: 2017, 6: 2018, 7: 2019})
	assert col2.describe_null == (3, 1)
	assert col2.dtype == (23, 64, 'u', '=')
	col3 = df.__dataframe__().get_column_by_name('weekday')
	assert col3.dtype[0] == _DtypeKind.CATEGORICAL
	assert col3.describe_categorical == (False, True, {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'})
	assert col3.describe_null == (3, 1)
	assert col3.dtype == (23, 64, 'u', '=')

	df2 = _from_dataframe_to_vaex(df.__dataframe__())
	assert  df2['colors'].tolist() == ['red', 'blue', 'green', 'blue']
	assert  df2['year'].tolist() == [2012, 2013, 2015, 2019]
	assert  df2['weekday'].tolist() == ['Mon', 'Tue', 'Fri', 'Sun']

	assert_dataframe_equal(df.__dataframe__(), df)

def test_arrow_dictionary():
	indices = pa.array([0, 1, 0, 1, 2, 0, 1, 2])
	dictionary = pa.array(['foo', 'bar', 'baz'])
	dict_array = pa.DictionaryArray.from_arrays(indices, dictionary)
	df = vaex.from_arrays(x = dict_array)

	# Some detailed testing for correctness of dtype and null handling:
	col = df.__dataframe__().get_column_by_name('x')
	assert col.dtype[0] == _DtypeKind.CATEGORICAL
	assert col.describe_categorical == (False, True, {0: 'foo', 1: 'bar', 2: 'baz'})
	assert col.describe_null == (3, 1)
	assert col.dtype == (23, 64, 'u', '=')

	df2 = _from_dataframe_to_vaex(df.__dataframe__())
	assert  df2.x.tolist() == df.x.tolist()
	assert df2.__dataframe__().get_column_by_name('x').null_count == 0

	assert_dataframe_equal(df.__dataframe__(), df)

def test_arrow_dictionary_missing():
	indices = pa.array([0, 1, 2, 0, 1], mask=np.array([0, 1, 1, 0, 0], dtype=bool))
	dictionary = pa.array(['aap', 'noot', 'mies'])
	dict_array = pa.DictionaryArray.from_arrays(indices, dictionary)
	df = vaex.from_arrays(x = dict_array)

	# Some detailed testing for correctness of dtype and null handling:
	col = df.__dataframe__().get_column_by_name('x')
	assert col.dtype[0] == _DtypeKind.CATEGORICAL
	assert col.describe_categorical == (False, True, {0: 'aap', 1: 'noot', 2: 'mies'})

	df2 = _from_dataframe_to_vaex(df.__dataframe__())
	assert  df2.x.tolist() == df.x.tolist()
	assert df2.__dataframe__().get_column_by_name('x').null_count == 2
	assert df['x'].dtype.index_type == df2['x'].dtype.index_type

	assert_dataframe_equal(df.__dataframe__(), df)

def test_string():
	df = vaex.from_dict({"A": ["a", "b", "cdef", "", "g"]})
	col = df.__dataframe__().get_column_by_name('A')

	assert col._col.tolist() == df.A.tolist()
	assert col.size == 5

	with pytest.raises(NotImplementedError):
	    assert col.dtype
	with pytest.raises(NotImplementedError):
	    assert col.describe_null

def test_object():
	df = vaex.from_arrays(x=np.array([None, True, False]))
	col = df.__dataframe__().get_column_by_name('x')

	assert col._col.tolist() == df.x.tolist()
	assert col.size == 3

	with pytest.raises(NotImplementedError):
	    assert col.dtype
	with pytest.raises(NotImplementedError):
	    assert col.describe_null

def test_virtual_column():
	df = vaex.from_arrays(
		x=np.array([True, True, False]),
		y=np.array([1, 2, 0]),
		z=np.array([9.2, 10.5, 11.8]))
	df.add_virtual_column("r", "sqrt(y**2 + z**2)")
	df2 = _from_dataframe_to_vaex(df.__dataframe__())
	assert  df2.r.tolist() == df.r.tolist()

def test_VaexBuffer():
	x = np.ndarray(shape=(5,), dtype=float, order='F')
	x_buffer = _VaexBuffer(x)

	assert x_buffer.bufsize == 5*x.itemsize
	assert x_buffer.ptr == x.__array_interface__['data'][0]
	assert x_buffer.__dlpack_device__() == (1, None)
	assert x_buffer.__repr__() == f"VaexBuffer({{'bufsize': {5*x.itemsize}, 'ptr': {x.__array_interface__['data'][0]}, 'device': 'CPU'}})"

	with pytest.raises(NotImplementedError):
		assert x_buffer.__dlpack__()

def test_VaexDataFrame():
	df = vaex.from_arrays(
		x=np.array([True, True, False]),
		y=np.array([1, 2, 0]),
		z=np.array([9.2, 10.5, 11.8]))

	df2 = df.__dataframe__()

	assert df2._allow_copy == True
	assert df2.num_columns() == 3
	assert df2.num_rows() == 3
	assert df2.num_chunks() == 1

	assert df2.column_names() == ['x', 'y', 'z']
	assert df2.get_column(0)._col.tolist() == df.x.tolist()
	assert df2.get_column_by_name('y')._col.tolist() == df.y.tolist()

	for col in df2.get_columns():
		assert col._col.tolist() == df[col._col.expression].tolist()

	assert df2.select_columns((0,2))._df[:,0].tolist() == df2.select_columns_by_name(('x','z'))._df[:,0].tolist()
	assert df2.select_columns((0,2))._df[:,1].tolist() == df2.select_columns_by_name(('x','z'))._df[:,1].tolist()

def assert_buffer_equal(buffer_dtype: Tuple[_VaexBuffer, Any], vaexcol:vaex.expression.Expression):
	buf, dtype = buffer_dtype
	pytest.raises(NotImplementedError, buf.__dlpack__)
	assert buf.__dlpack_device__() == (1, None)
	assert dtype[1] == vaexcol.dtype.numpy.itemsize * 8
	if not isinstance(vaexcol.values, np.ndarray) and isinstance(vaexcol.values.type, pa.DictionaryType):
		assert dtype[2] == vaexcol.index_values().dtype.numpy.str
	else:
		assert dtype[2] == vaexcol.dtype.numpy.str 

def assert_column_equal(col: _VaexColumn, vaexcol:vaex.expression.Expression):
	assert col.size == vaexcol.df.count("*") 
	assert col.offset == 0
	assert col.null_count == vaexcol.countmissing()
	assert_buffer_equal(col._get_data_buffer(), vaexcol)

def assert_dataframe_equal(dfo: DataFrameObject, df:vaex.dataframe.DataFrame):
	assert dfo.num_columns() == len(df.columns)
	assert dfo.num_rows() == len(df)
	assert dfo.column_names() == list(df.get_column_names())
	for col in df.get_column_names():
		assert_column_equal(dfo.get_column_by_name(col), df[col])
