
ctypedef unsigned long long uint64_t
from libc.stdlib cimport malloc, free

__all__ = ("sampling_bbox", )

cpdef sampling_bbox(unsigned char* data, uint64_t width, uint64_t height, uint64_t bands, bbox, cb, index):
    cdef uint64_t b_left, b_top, b_width, b_height
    
    b_left, b_top, b_width, b_height = bbox
    
    cdef uint64_t offset_base, offset_row, offset_x, offset_y, offset, i
    cdef uint64_t* output = <uint64_t*>malloc(bands * sizeof(uint64_t *))
    
    for i from 0 <= i < bands:
        output[i] = 0
    
    with nogil:
        offset_base = b_top * width + b_left
        offset_y = 0
        
        for offset_y from 0 <= offset_y < (b_height - b_top):
            offset_row = offset_base + width * offset_y
            
            for offset_x from 0 <= offset_x < (b_width - b_left):
                offset = (offset_row + offset_x) * bands
                
                for i from 0 <= i < bands:
                    output[i] += data[offset + i]
    
    py_output = [output[i] for i in range(bands)]
    free(output)
    cb(index, py_output)
