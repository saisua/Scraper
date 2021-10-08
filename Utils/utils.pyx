# Internal cimports
cimport cython

from cpython.ref cimport PyObject
from cython.operator cimport dereference

from libc.stdlib cimport malloc, free
from libc.string cimport strcmp

from libcpp.string cimport string as cstr
from libcpp.unordered_map cimport unordered_map as cumap # C-unordered map
from libcpp.vector cimport vector

# External declarations
cdef extern from "Python.h":
    char* PyUnicode_AsUTF8(object unicode)


"""
    This file contains functions based of optimized Cython code
    to cast Python objects w/o relying on Python casting

    I don't know if it would be better, but to get from a str
    to a bytes object in python you have call a pytohn function,
    passing as an argument a string. That looks slow to me.

    I know you shouldn't inline loops, but the performance is meant
    to be as high as possible.
"""

@cython.wraparound(False)
@cython.boundscheck(False)
cpdef public inline cstr to_cstring(str data):
    cdef char *result = <char *>malloc(len(data) * sizeof(char *))
    
    cdef int index
    cdef str letter
    for index, letter in enumerate(data):
        result[index] = dereference(PyUnicode_AsUTF8(letter))
    return cstr(result)

@cython.wraparound(False)
@cython.boundscheck(False)
cpdef public inline vector[cstr] multi_to_cstring(list data):
    cdef vector[cstr] result = vector[cstr](len(data))

    cdef char *tmp_string

    cdef int v_index, s_index
    cdef str element
    cdef str letter

    for index, element in enumerate(data):
        tmp_string = <char *>malloc(len(element) * sizeof(char *))

        for index, letter in enumerate(element):
            tmp_string[index] = dereference(PyUnicode_AsUTF8(letter))
        
        result[index] = cstr(tmp_string)
    
    return result

"""
@cython.wraparound(False)
@cython.boundscheck(False)
cdef vector[PyObject*] to_vector(list data):
    cdef vector[PyObject*] result = vector[PyObject](len(data))

    cdef int index
    cdef object element
    for index, element in enumerate(data):
        result[index] = element
    
    return result

@cython.wraparound(False)
@cython.boundscheck(False)
cdef cumap to_cumap(dict data):
    cdef cumap result = cumap[object, object]()

    cdef object key, value
    for key, value in data.items():
        result[key] = value

    return result
"""