
ctypedef unsigned long long uint64_t

__all__ = ("diff_buffer", "merge_buffer")

cpdef diff_buffer(unsigned char* data, const unsigned char* ref_data, uint64_t length):
    cdef uint64_t i
    with nogil:
        for i from 0 <= i < length:
            data[i] = data[i] - ref_data[i]

cpdef merge_buffer(unsigned char* data, const unsigned char* ref_data, uint64_t length):
    cdef uint64_t i
    with nogil:
        for i from 0 <= i < length:
            data[i] = data[i] + ref_data[i]
    
