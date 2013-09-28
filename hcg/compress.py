
__all__ = ("diff_buffer", "merge_buffer")

def diff_buffer(data, ref_data, length):
    i = 0
    while i < length:
        _ = data[i] - ref_data[i]
        if _ < 0: _ += 256
        data[i] = _
        i += 1

def merge_buffer(data, ref_data, length):
    i = 0
    while i < length:
        data[i] = (data[i] + ref_data[i]) % 256
        i += 1

