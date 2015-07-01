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
                        "ROUTE"         : "US",
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

POST_DIRECTIONS = ["NB", "SB", "EB", "WB"]

POST_DIR_TRANS = {"NORTHBOUND"   : "NB", "SOUTHBOUND"  : "SB",
                  "EASTBOUND"    : "EB", "WESTBOUND"   : "WB",
                   "NORTH BOUND" : "NB", "SOUTH BOUND" : "SB",
                   "EAST BOUND"  : "EB", "WEST BOUND"  : "WB",
                   "NORTH-BOUND" : "NB", "SOUTH-BOUND" : "SB",
                   "EAST-BOUND"  : "EB", "WEST-BOUND"  : "WB"}

def sanitize(user_input):
    # I'm sure this could be done better
    clean = re.sub(r"[;\(\)\[\]\<\>=:*\%\$\`\?]", "", user_input)
    return clean

def parsed_list_to_dict(parsed_address):
    for part in parsed_address:
        print part
    raise NotImplementedError("parsed_list_to_dict not yet implemented")

def construct_query(parsed_address):
    if not parsed_address:
        raise Exception("Parser did not return a valid response")

    if type(parsed_address) is list:
        address_parts = parsed_list_to_dict(parsed_address)
    else:
        parse_result_type = parsed_address[1]

        if parse_result_type == 'ambiguous':
            raise ValueError("Not a valid address")

        if not parse_result_type == 'Street Address':
            raise Exception("Parser results are confusing")

        address_parts = parsed_address[0]

    clause_list = []

    if 'AddressNumber' in address_parts:
        value = address_parts['AddressNumber']
        #clause = "address > {} and address < {}"
        #clause_list.append(clause.format(int(value)-100, int(value)+100))
        clause_list.append("address = {}".format(value))

    if 'AddressNumberSuffix' in address_parts:
        value = address_parts['AddressNumberSuffix'].upper()
        clause_list.append("address_fr = '{}'".format(value))

    if 'StreetNamePreDirectional' in address_parts:
        value = address_parts['StreetNamePreDirectional'].upper()

        if value in STREET_PRE_DIR_TRANS.keys():
            value = STREET_PRE_DIR_TRANS[value]

        clause_list.append("prefix_dir = '{}'".format(value))

    if 'StreetNamePreType' in address_parts:
        value = address_parts['StreetNamePreType'].upper()

        if value == "ROUTE":
            value = "US"

        clause_list.append("prefix_typ = '{}'".format(value))

    if 'StreetName' in address_parts:
        value = address_parts['StreetName'].upper()
        clause_list.append("street_nam = '{}'".format(value))

    if 'StreetNamePostType' in address_parts:
        value = address_parts['StreetNamePostType'].upper()

        if value in POST_DIRECTIONS:
            clause_list.append("suffix_dir = '{}'".format(value))
        else:
            clause_list.append("street_typ = '{}'".format(value))

    if 'StreetNamePostDirectional' in address_parts:
        value = address_parts['StreetNamePostDirectional'].upper()
        clause_list.append("suffix_dir = '{}'".format(value))

    if len(clause_list) <= 0:
        raise Exception("Invalid address")

    query = "select * from address_point where "
    query += clause_list[0]

    for clause in clause_list[1:-1]:
        query += " and " + clause

    return query
    #return "select * from address_point where address = 100 and street_nam = 'lamar'"

def score_results(result_table):
    candidates_json = ""
    return candidates_json

def query_db(query):
    address_shp = r"shapefiles/address_point/address_point.shp"
    driver = ogr.GetDriverByName('ESRI Shapefile')
    data_source = driver.Open(address_shp, 0)
    table = data_source.ExecuteSQL(query)

    for row in table:
        field_index = row.GetFieldIndex('FULL_STREE')
        print row.GetFieldAsString(field_index)

    return table

def locate(address_string):
    clean_string = sanitize(address_string)

    # handle an edge case with US before parsing
    if "US " in clean_string:
        clean_string.replace("US ", "ROUTE")

    parse_result = usaddress.tag(clean_string)
    query = construct_query(parse_result)
    result_table = query_db(query)
    candidates_json = score_results(result_table)
    return candidates_json

def main(address_string):
    candidates_json = locate(address_string)
    print candidates_json

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
