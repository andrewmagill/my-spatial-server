import mmap, struct

class bcolors:
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    CYAN = '\033[36m'
    BLUE = '\033[94m'
    DARKGRAY = '\033[90m'
    LIGHTRED = '\033[91m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'

def explode_bundle(file_path):
    """given the path to a bundle file, finds all
    embedded png and writes each out to disk"""
    with open(file_path, "r+b") as f:
        # memory-map the file, size 0 means whole file
        mm = mmap.mmap(f.fileno(), 0)

        png_header_string = "\211PNG\r\n\032\n"
        begin_read = 0
        count = 0

        # try not to fill up hd
        while count < 2000:

            begin_read = mm.find(png_header_string, begin_read)

            if begin_read < 0:
                break

            size = struct.unpack('i',mm[begin_read - 4:begin_read])[0]
            end_read = begin_read + size

            count += 1
            output_file = open("tile_%i.png" % count, 'wb')
            output_file.write(mm[begin_read:end_read])
            output_file.close()

            begin_read = end_read

        # close the map
        mm.close()

def parse_bundlx(file_path):
    with open(file_path, "r+b") as f:
        # memory-map the file, size 0 means whole file
        mm = mmap.mmap(f.fileno(), 0)

        start_byte  = 16
        block_size  = 320
        line_size   = 16
        dword_size  = 4
        byte_count  = start_byte

        for read_from in range(start_byte, len(mm), block_size):

            block = mm[read_from:read_from + block_size]

            for read_from in range(0, len(block), line_size):

                line = block[read_from:read_from + line_size]

                for read_from in range(0, len(line), dword_size):

                    if not read_from == 0:
                        print bcolors.DARKGRAY + "|" + bcolors.ENDC,

                    dword = line[read_from:read_from + dword_size]

                    for byte in dword:

                        block_pos = (byte_count - start_byte) % block_size
                        previous = mm[byte_count - block_size]
                        d = int(byte.encode('hex'), 16)

                        if not byte == previous:
                            if ((block_pos - 1) % 5) == 0:
                                text_color = bcolors.YELLOW
                            else:
                                text_color = bcolors.LIGHTRED

                            print text_color + \
                                  byte.encode('hex') + \
                                  bcolors.DARKGRAY + '..' + \
                                  bcolors.ENDC,
                        elif d >=  32 and d <= 127:
                            print bcolors.PURPLE + " " + \
                                  byte.encode('ascii') + \
                                  bcolors.DARKGRAY + \
                                  byte.encode('hex') + \
                                  bcolors.ENDC,
                        else:
                            print bcolors.CYAN + \
                                  byte.encode('hex') + \
                                  bcolors.DARKGRAY + '..' + \
                                  bcolors.ENDC,

                        byte_count += 1

                line_no = (byte_count / line_size)
                print bcolors.DARKGRAY + "\t%x" % line_no + bcolors.ENDC
            print

        mm.close()

def main():
    bundle_file_path = r"files/R0480C0380.bundle"
    bundle_index_path = r"files/R0480C0380.bundlx"

    #explode_bundle(bundle_file_path)
    parse_bundlx(bundle_index_path)

if __name__== "__main__":
    main()
