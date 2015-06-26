import os, mmap, re, struct

class bcolors:
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    CYAN = '\033[36m'
    LIGHTBLUE = '\033[34m'
    BLUE = '\033[94m'
    LIGHTGRAY = '\033[37m'
    DARKGRAY = '\033[90m'
    LIGHTRED = '\033[91m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    ONWHITE = '\033[48m'
    WHITE = '\033[37m'

class Cache(object):
    """Represents a map tile cache"""

    MAX_ROWS    = 128
    MAX_COLUMNS = 128

    MIN_DIGITS_LEVEL = 1
    MAX_DIGITS_LEVEL = 3

    BUNDLX = ".bundlx"

    def __init__(self, root_path):
        self.root_path = root_path
        self.levels    = {}
        self.bundles   = []
        self._find_bundles()

    def get_bundle(self, level, row, column):
        """Returns the bundle, if one exists, that would contain a tile,
        if one exists, for the given level, row, and column.
        """
        # this breaks the whole max_digits_level flexibility thing
        level = "L%02d" % level
        if not self.levels.has_key(level):
            raise Exception('Level %s does not exist in cache' % level)

        bundles = self.bundles[self.levels[level]]


        for bundle in bundles:
            bundle_row, bundle_col = self._extract_row_col(bundle)
            if bundle_row > row:
                continue
            if bundle_col > column:
                continue
            if bundle_row > row - Cache.MAX_ROWS:
                if bundle_col > column - Cache.MAX_COLUMNS:
                    return bundle


    def _extract_level(self, path):
        """Returns substring like 'L00', or 'L01', if it exists"""
        m = Cache.MIN_DIGITS_LEVEL
        n = Cache.MAX_DIGITS_LEVEL
        match = re.search('L[0-9]{%i,%i}' % (m,n), path)
        if match:
            return match.group(0)

    def _is_cache_path(self, path):
        """Check root_path for 'Layers', '_alllayers',
        or some folder like 'L00'.  Returns boolean.
        """
        contents = os.listdir(path)
        if contents.count("Layers"):
            return True
        elif contents.count("layers"):
            return True
        elif contents.count("_alllayers"):
            return True

        for item in contents:
            if self._extract_level(item):
                return True

        return False

    def _extract_row_col(self, file_name):
        """Returns row and column integer for given bundle name."""

        # Regex Match all characters between two strings
        # http://stackoverflow.com/a/6110113/1344499
        row_match = re.search('(?<=R)(.*)(?=C)', file_name)
        if not row_match:
            raise Exception('Not a bundle file')

        col_match = re.search('[^C]+$', file_name)
        if not col_match:
            raise Exception('Not a bundle file')

        row_hex = row_match.group(0)
        col_hex = col_match.group(0)

        row_int = int(row_hex, 16)
        col_int = int(col_hex, 16)
        return row_int, col_int

    def _find_bundles(self):
        """Searches root_path for bundlx files, populates
        levels hash with level name and index corresponding
        to second-dimensional list in bundles.

        ex:
            self.levels might contain
                {'L00': 0,'L00': 1,'L00': 2,'L00': 3}
            self.bundles would be like this
                [[R01C01],
                 [R02C02],
                 [R04C04,R04C04],
                 [R05C04,R06C04,R05C05,R06C05]]

            (of course the bundle names would differ)

        Could probably be done way better.
        """
        if not os.path.isdir(self.root_path):
            raise Exception("Directory does not exist")

        if not self._is_cache_path(self.root_path):
            raise Exception("Directory does not appear \
                             to contain a map cache")

        for root, dirs, files in os.walk(self.root_path):

            for file in files:

                file_path = os.path.join(root, file)
                file_name, file_ext = os.path.splitext(file_path)

                if not file_ext == Cache.BUNDLX:
                    continue

                level = self._extract_level(file_path)

                if not self.levels.has_key(level):
                    self.levels[level] = len(self.bundles)

                index = self.levels[level]

                #bundle_tuple = (file_name, self._extract_row_col(file_name))
                #
                #if index >= len(self.bundles):
                #    self.bundles.append([bundle_tuple])
                #else:
                #    self.bundles[index].append(bundle_tuple)
                if index >= len(self.bundles):
                    self.bundles.append([file_name])
                else:
                    self.bundles[index].append(file_name)

class Tile(object):
    """Represents a map tile image with associated attributes:

    level   -   zoom level in which the image is displayed
    row     -   row in which the image is displayed
    column  -   column in which the image is displayed
    bundle  -   name of bundle file that contains the image
    path    -   unc path where bundle file is located
    address -   byte address of the image data in the bundle file
    """
    def __init__(self, path=None, level=None, row=None,
                 column=None, **kwargs):
        """Initializes the Tile object"""
        self.path    = path
        self.level   = level
        self.row     = row
        self.column  = column
        self.bundle  = None
        self.address = None
        self.image   = None

    def image(self):
        """Returns image if found, raises Exception if not found"""
        if not self.image:
            try:
                self._get_image()
            except Exception as e:
                raise e

    def _get_image():
        pass


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

def compare_bundlx(file_path1, file_path2):
    file1 = open(file_path1, "r+b")
    file2 = open(file_path2, "r+b")

    mm1 = mmap.mmap(file1.fileno(), 0)
    mm2 = mmap.mmap(file2.fileno(), 0)

    for i in range(len(mm1)):

        byte1 = mm1[i]
        byte2 = mm2[i]

        h1 = byte1.encode('hex')
        h2 = byte2.encode('hex')

        d1 = int(h1, 16)
        d2 = int(h2, 16)

        if d1 >= 32 and d1 <= 127:
            char1 = byte1.encode('ascii').ljust(2)
        else:
            char1 = h1

        if d2 >= 32 and d2 <= 127:
            char2 = byte2.encode('ascii').ljust(2)
        else:
            char2 = h2


        if mm1[i] == mm2[i]:
            if char1 == '00':
                print bcolors.CYAN + "%s" % char1 + bcolors.ENDC,
                print bcolors.CYAN + "%s" % char2 + bcolors.ENDC,
            else:
                print bcolors.LIGHTBLUE + "%s" % char1,
                print bcolors.LIGHTBLUE + "%s" % char2 + bcolors.ENDC,
        else:
            print bcolors.WHITE + "%s" % char1 + bcolors.ENDC,
            print bcolors.WHITE + "%s" % char2 + bcolors.ENDC,

        offset = i + 1

        if offset % 16 == 0:
            if not offset == 0:
                print bcolors.DARKGRAY + "   %x " % i + bcolors.ENDC
        elif offset % 4 == 0:
            print bcolors.LIGHTGRAY + ':' + bcolors.ENDC,
            #try:
            #    m1 = int(str(mm2[i]), 16)
            #    m2 = int(str(mm2[i]), 16)
            #    m3 = int(str(mm2[i]), 16)
            #    m4 = int(str(mm2[i]), 16)
            #    print "%i %i %i %i" % (m1,m2,m3,m4),
            #except:
            #    pass
        else:
            print bcolors.DARKGRAY + ':' + bcolors.ENDC,

        if (offset - 16) % 320 == 0:
            for x in range(16):
                print bcolors.DARKGRAY + "    %x  " % (x) + bcolors.ENDC,
            #print
            raw_input()

def parse_bundlx(file_path):
    with open(file_path, "r+b") as f:
        # memory-map the file, size 0 means whole file
        mm = mmap.mmap(f.fileno(), 0)

        start_byte  = 16
        block_size  = 320
        line_size   = 16
        dword_size  = 4
        byte_count  = start_byte
        line_no = 0

        for read_from in range(start_byte, len(mm), block_size):

            block = mm[read_from:read_from + block_size]

            temp_list = []

            for read_from in range(0, len(block), line_size):

                line = block[read_from:read_from + line_size]

                for read_from in range(0, len(line), dword_size):

                    #if not read_from == 0:
                    #    print bcolors.DARKGRAY + "|" + bcolors.ENDC,

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
                                temp_list.append((byte, line_no, block_pos, byte_count))
                            pass
                            #print text_color + \
                            #      byte.encode('hex') + \
                            #      bcolors.DARKGRAY + '..' + \
                            #      bcolors.ENDC,
                        elif d >=  32 and d <= 127:
                            pass
                            #print bcolors.PURPLE + " " + \
                            #      byte.encode('ascii') + \
                            #      bcolors.DARKGRAY + \
                            #      byte.encode('hex') + \
                            #      bcolors.ENDC,
                        else:
                            pass
                            #print bcolors.CYAN + \
                            #      byte.encode('hex') + \
                            #      bcolors.DARKGRAY + '..' + \
                            #      bcolors.ENDC,

                        byte_count += 1

                line_no = (byte_count / line_size)
                #print bcolors.DARKGRAY + "\t%x" % line_no + bcolors.ENDC,
            #print

            for item, line, position, count in temp_list:
                if not item.encode('hex') == '00':
                    try:
                        char = bcolors.YELLOW + item.encode('ascii') + bcolors.DARKGRAY + " %x:%i:%x " % (line, position, count)
                    except:
                        char = bcolors.YELLOW + item.encode('hex') + bcolors.DARKGRAY + " %x:%i:%x " % (line, position, count)

                    print char,
            #print

        mm.close()

def blablabla(file_path):
    file = open(file_path, "r+b")

    mm = mmap.mmap(file.fileno(), 0)

    magic_nos = []
    stored_value = 0
    previous_stored_value = 0

    for i in range(len(mm)):

        offset = i

        byte = mm[i]
        base16 = byte.encode('hex')
        base10 = int(base16, 16)

        magic_nos.append(base10)

        print bcolors.BLUE + "%03d" % base10 + bcolors.ENDC,

        if offset % 5 == 0:
            if not offset == 0:
                try:
                    stored_value = magic_nos[0] * 1
                    stored_value += magic_nos[1] * 256
                    stored_value += magic_nos[2] * 65536
                    stored_value += magic_nos[3] * 16777216
                    stored_value += magic_nos[4] * 4294967296
                    if not stored_value == (previous_stored_value + 4):
                        print bcolors.LIGHTRED + " %i" % stored_value + bcolors.ENDC
                    else:
                        print bcolors.DARKGRAY + " %i" % stored_value + bcolors.ENDC
                except Exception as e:
                    print

                magic_nos = []
                previous_stored_value = stored_value
                stored_value = 0

def chunk(file_path):
    """Chunk returns a list of decimal values stored in a .bundlx (bundle
    index) file that represent the locations of images stored in the
    corresponding .bundle file.

    The values are stored in 5 byte chunks using little endian representation
    to store large numbers.  Each .bundlx file is exactly the same size; the
    position of each chunk in the .bundlx indicates the row and column position
    of the particular map tile image in the overall scheme.  These values
    should be added to the top left origin row and column found in the bundle
    file name.

    Each chunk contains at least two bytes.  The first byte represents the row,
    the second represents the column.  However, only 'blank' chunks represent
    the row and column!  Non blank chunks use all 5 byts to represent the
    postition of the image in the .bundle file.

    It is up to the developer to determine what to do with the bogus values
    found in the 'blank' chunks.
    """
    file = open(file_path, "r+b")

    mm = mmap.mmap(file.fileno(), 0)

    chunk_bytes = []

    for i in range(len(mm)):

        byte = mm[i]
        base16 = byte.encode('hex')
        base10 = int(base16, 16)

        chunk_bytes.append(base10)

        if i % 5 == 0:
            if not i == 0:
                # decimal value is store using
                # little endian representation
                stored_value  = chunk_bytes[0] * 1
                stored_value += chunk_bytes[1] * 256
                stored_value += chunk_bytes[2] * 65536
                stored_value += chunk_bytes[3] * 16777216
                stored_value += chunk_bytes[4] * 4294967296

                chunk_bytes = []
                # this doesn't really need to happen, but
                # just for good measure, set value to zero
                stored_value = 0

    return chunk_bytes

def find_bundle(level, row, column):
    pass

def get_tile(level, row, column, root_directory):
    """Returns a tile object containing an image corresponding to the
    level, row, and columns passed as parameters, if an image is found
    in a bundle file under the root directory (also passed to function).
    """
    pass

def main():
    bundles = ["files/L00/R0480C0380.bundlx",
               "files/L01/R0900C0700.bundlx",
               "files/L02/R1280C0e80.bundlx",
               "files/L03/R2500C1d00.bundlx",
              ["files/L04/R4a00C3a00.bundlx",
               "files/L04/R4a00C3a80.bundlx"],
              ["files/L05/R9400C7480.bundlx",
               "files/L05/R9400C7500.bundlx",
               "files/L05/R9480C7480.bundlx",
               "files/L05/R9480C7500.bundlx"],
               "files/R251f80C1d4700.bundlx"]

    # Level 0
    #   R         C
    #   0480      0380
    # Level 1
    #   R         C
    #   0900      0700
    # Level 2
    #   R         C
    #   1280      0e80
    # Level 3
    #   R         C
    #   2500      1d00
    # Level 4
    #   R         C
    #   4a00      3a00
    #   4a00      3a80
    # Level 5
    #   R         C
    #   9400      7480
    #   9400      7500
    #   9480      7480
    #   9480      7500
    #   .
    #   .
    #   .
    # Level 11
    #   R         C
    #   . . .
    #   251f80    1d4700
    #   . . .


    #explode_bundle(bundle_file_path)
    #parse_bundlx(bundle_index_path)
    #compare_bundlx(bundles[0], bundles[-1])
    blablabla(bundles[0])

if __name__== "__main__":
    main()
