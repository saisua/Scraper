cimport cython

from libcpp.string cimport string as cstr
from libcpp.vector cimport vector

cpdef public inline cstr to_cstring(str data)

cpdef public inline vector[cstr] multi_to_cstring(list data)