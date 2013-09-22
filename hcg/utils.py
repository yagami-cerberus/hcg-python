
__all__ = ["BytesIO", "evaluate_image_diff", "sampling_bbox", "split_rect"]

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

try:
    range = xrange
except NameError:
    pass

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
    
def sampling_bbox(data, width, height, bbox):
    data_avg = [0 for i in range(len(data[0]))]
    
    posx, posy = bbox[0], bbox[1]
    sampx, sampy = bbox[2], bbox[3]
    
    base_offset = posy * width + posx
    for offset_y in range(sampy - posy):
        row_offset = base_offset + width * offset_y
        
        for offset_x in range(sampx - posx):
            pixel = data[row_offset + offset_x]
            
            for idx in range(len(pixel)):
                data_avg[idx] += pixel[idx]
    
    return data_avg

def split_rect(width, height):
    for y_bound in split_line(height):
        for x_bound in split_line(width):
            yield (x_bound[0], y_bound[0], x_bound[1], y_bound[1])

def split_line(length):
    segement = int(round(length / 100.0, 0))
    fixed_length = length // segement
    
    for i in range(segement - 1):
        yield (fixed_length*i, fixed_length*(i+1))
    
    yield (fixed_length*(segement - 1), length)

