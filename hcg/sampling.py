
import sys

try:
    range = xrange
except NameError:
    pass

__all__ = ["evaluate_image_diff", "sampling_bbox", "split_rect"]


def evaluate_image_diff(image1, image2):
    ziped_sample = zip(image1.sample, image2.sample)

    elements = []
    for s1, s2 in ziped_sample:
        for e1, e2 in zip(s1, s2):
            elements.append(e1 - e2)

    summation = sum(elements)
    total = float(len(elements))
    average = summation / total

    err = sum((average - e)**2 for e in elements)
    return (err/total)**0.5

def sampling_bbox(data, width, height, bands, bbox, cb, index):
    try:
        b_left, b_top, b_width, b_height = bbox
        
        output = [0 for i in range(bands)]
        
        base_offset = b_top * width + b_left
        for offset_y in range(b_height - b_top):
            row_offset = base_offset + width * offset_y
    
            for offset_x in range(b_width - b_left):
                offset = (row_offset + offset_x) * bands
                
                for i in range(bands):
                    output[i] += data[offset + i]

    except Exception:
        cb(index, sys.exc_info())
        raise

    cb(index, output)

def split_rect(width, height):
    for y_bound in split_line(height):
        for x_bound in split_line(width):
            yield (x_bound[0], y_bound[0], x_bound[1], y_bound[1])

def split_line(length):
    segement = int(round(length / 100.0, 0))
    
    if segement == 0:
        segement = 1
    
    fixed_length = length // segement
    
    for i in range(segement - 1):
        yield (fixed_length*i, fixed_length*(i+1))
    
    yield (fixed_length*(segement - 1), length)

