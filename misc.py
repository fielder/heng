def chopSequence(sequence, chunksize):
    idx = 0
    while idx < len(sequence):
        yield sequence[idx:idx + chunksize]
        idx += chunksize
