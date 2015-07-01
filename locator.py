import sys
from osgeo import ogr
import usaddress
import re, string

STREET_PRE_DIR_TRANS = {"NORTH" : "N",
                        "SOUTH" : "S",
                        "EAST"  : "E",
                        "WEST"  : "W"}

STREET_PRE_TYPES = ["US", "IH", "SH", "CR", "FM", "RR"]

STREET_PRE_TYPE_TRANS = {"INTERSTATE"    : "IH",
                        "STATE HIGHWAY" : "SH",
                        "US ROUTE"      : "US",
                        "US ROAD"       : "US",
                        "FARM ROAD"     : "FM",
                        "RANCH ROAD"    : "RR",
                        "FARM TO MARKET": "FM",
                        "COUNTY RD"     : "CR"}

STREET_PRE_TYPE_TROUBLE = {"FARM"  : "FM", "RANCH"  : "RR",
                           "STATE" : "SH", "COUNTY" : "CR"}

STREET_POST_TYPES = ["RD", "DR", "ST", "BLVD", "LN", "TRL", "CIR", "CT",
                     "WAY", "HWY", "HIGHWAY", "RUN"]

STREET_POST_TYPE_TRANS = {"ROAD"      : "RD",
                          "DRIVE"     : "DR",
                          "STREET"    : "ST",
                          "BOULEVARD" : "BLVD",
                          "LANE"      : "LN",
                          "TRAIL"     : "TRL",
                          "CIRCLE"    : "CIR",
                          "HIGHWAY"   : "HWY",
                          "COURT"     : "CT"}

POST_DIRECTIONS = ["NB", "SB", "EB", 'WB"]

POST_DIR_TRANS = {"NORTHBOUND"   : "NB", "SOUTHBOUND"  : "SB",
                  "EASTBOUND"    : "EB", "WESTBOUND"   : "WB",
                   "NORTH BOUND" : "NB", "SOUTH BOUND" : "SB",
                   "EAST BOUND"  : "EB", "WEST BOUND"  : "WB",
                   "NORTH-BOUND" : "NB", "SOUTH-BOUND" : "SB",
                   "EAST-BOUND"  : "EB", "WEST-BOUND"  : "WB"]

def sanitize(user_input):
    # I'm sure this could be done better
    clean = re.sub(r"[;\(\)\[\]\<\>=:*\%\$\`\?]", "", user_input)
    return clean

def parsed_list_to_dict(parsed_address):
    for part in parsed_address:
        print part
    raise NotImplementedError("parsed_list_to_dict not yet implemented")

def construct_query(parsed_address):
    if not parse_result:
        raise Exception("Parser did not return a valid response")

    if type(parsed_address) is list:
        address_parts = parsed_list_to_dict(parsed_address)
    else:
        parse_result_type = parse_result[1]

        if parse_result_type == 'ambiguous':
            raise ValueError("Not a valid address")

        if not parse_result_type == 'Street Address':
            raise Exception("Parser results are confusing")

        address_parts = parse_result[0]

    clause_list = []

    if 'AddressNumber' in address_parts:
        value = address_parts['AddressNumber']
        clause = "address > {} and address < {}"
        clause_list.append(clause.format(value-100, value+100))

    if 'AddressNumberSuffix' in address_parts:
        value = address_parts['AddressNumberSuffix'].upper()
        clause_list.append("address_fr = {}".format(value))

    if 'StreetNamePreDirectional' in address_parts:
        value = address_parts['StreetNamePreDirectional'].upper()

        if value in STREET_PRE_DIR_TRANS.keys():
            value = STREET_PRE_DIR_TRANS[value]

        clause_list.append("prefix_dir = {}".format(value))

    # logic gets a little messy here to account for occasional parsing
    # errors. i haven't tried training the parser on my data, that might work.

    # we want to check to see if th parser picked up a street name. if it
    # did not, the street name might actually be hiding in the prefix type

    # we want:
    # (u'PREFIX_TYP', u'US'), (u'STREET_NAM', u'183'), (u'STREET_TYP', u'HWY')
    # not:
    # ('StreetNamePreType', u'US 183 HWY')])

    # if there is a street name, it might incorrectly include the street type,
    # as seen in the example above. this also seems to happen when a post
    # direction is present in the address. we will need to remove the street
    # type from the name, set it as the post type, and set the direction
    # (nb, sb, etc), if present, to the post dir

    if 'StreetName' in address_parts:
        # check to see if street name includes street type

    else: # no street name
        # check to see if there is a pre type. if the length of the
        # pre type is > 2, then it's probably holding more than the pre type
        if 'StreetNamePreType' in address_parts:
            pre_type = address_parts['StreetNamePreType'].upper()
            if len(pre_type) > 2:
                pre_type_parts= pre_type.split(" ")
                if pre_type_parts[0] in STREET_PRE_TYPES
                    clause_list.append(prefix_typ = pre_type_parts[0])




    if not 'StreetName' in address_parts:
            if 'StreetNamePreType' in address_parts:
                value = address_parts['StreetNamePreType'].upper()

    if 'StreetNamePreType' in address_parts:
        value = address_parts['StreetNamePreType'].upper()
        if not 'StreetName' in address_parts:
            clause_list.append("street_name = {}".format(value))
            #print address_parts['StreetNamePreType']
        else:
            clause_list.append("prefix_typ = {}".format(value))
            #print address_parts['StreetNamePreType']

    # frequent edge case:
    # parser sets StreetPostType to the post direction (nb, sb, ...)
    # and the actual post type becomes part of the street name
    # i'm attempting to check for such cases and set things to
    # the correct fields.
    # ie: StreetName = "Hank Rd", StreetPostType = "SB"
    # becomes: StreetName = "Hank", StreetPostType = "Rd", StreetPostDir = "SB"
    if 'StreetNamePostType' in address_parts:
        post_type_value = address_parts['StreetNamePostType'].upper()
        # post type should be st, or rd, not nb, or sb
        if post_type_value in POST_DIRECTIONS:
            # check to see if the type was included in the street name
            if 'StreetName' in address_parts:
                value = address_parts['StreetName'].upper()
                value_parts = value.split(" ")
                if len(value_parts) > 1:
                    # check the last word in street name, determine if it's
                    # actually a street type and should not be part of the name
                    if value_parts[-1] in STREET_TYPES
                        value = " ".join(value_parts[:len(value_parts)-1])
                        clause_list.append("STREET_TYP = {}".format(value))
        else:
            # post type was not a post direction, so we'll use the
            # value to query SUFFIX_DIR. This is the best case.
            clause_list.append("street_name = {}".format(value))


    if 'StreetName' in address_parts:
        value = address_parts['StreetName'].upper()
        clause_list.append("street_name = {}".format(value))

    if 'StreetNamePostType' in address_parts:
        value = address_parts['StreetNamePostType'].upper()
        clause_list.append("STREET_TYP = {}".format(value))

    if 'StreetNamePostType' in address_parts:
        value = address_parts['StreetNamePostType'].upper()
        clause_list.append("suffix_dir = {}".format(value))

    if len(clause_list) <= 0:
        raise Exception("Invalid address")

    query = "select * from address_point where"
    query += clause_list[0]

    for clause in clause_list[1:-1]:
        query += " and " + clause

    return query + ";"

def score_results(result_table):
    candidates_json = ""
    return candidates_json

def query_db(query):
    address_shp = r"shapefiles/address_point/address_point.shp"
    driver = ogr.GetDriverByName('ESRI Shapefile')
    data_source = driver.Open(address_shp, 0)

def locate(address_string):
    clean_string = sanitize(address_string)
    parse_result = usaddress.tag(clean_string)
    query = construct_query(parse_result)
    result_table = query_db(query)
    canidates_json = score_results(result_table)
    return json

def main(address_string):
    locate(address_string)
    print json

if __name__ == "__main__":
    main(sys.argv[1])

#OrderedDict([(u'ADDRESS', 14521),
#(u'PREFIX_DIR', u''),
#(u'PREFIX_TYP', u''),
#(u'STREET_NAM', u'WHARTON PARK'),
#(u'STREET_TYP', u'TRL'),
#(u'ADDRESS_TY', 4),
#(u'SUFFIX_DIR', u''),
#(u'PARENT_PLA', 3032691),
#(u'PLACE_ID', 3127555),
#(u'SEGMENT_ID', 2036823),
#(u'ADDRESS_FR', u'1/2'),
#(u'ADDRESS_SU', u''),
#(u'FULL_STREE', u'14521 1/2 WHARTON PARK TRL'),
#(u'CREATED_BY', u'GIS-mclement'),
#(u'CREATED_DA', datetime.date(2004, 5, 6)),
#(u'MODIFIED_B', u'RMANOR'),
#(u'MODIFIED_D', datetime.date(2005, 11, 30))])
