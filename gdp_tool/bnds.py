def extract_bounds(bnds):
    bnds = bnds.split(',')
    bounds = []
    try:
	    for b in bnds:
	        b = b.split("..")
	        if len(b) > 1:
	            bounds.append((int(b[0]), int(b[1])))
	        else:
	            bounds.append((int(b[0]), int(b[0])+1))
    except ValueError:
        print("error: generator bounds must be defined as integers or as integer ranges")
        print("examples of correct input:\n    2..4,3..5,1..4\n    3,4,2..4\n    3..7,2\n    4")
        exit()
    for b in bounds:
        if b[0] > b[1]:
            print(f"error: range {b[0]}..{b[1]} is not well formed (range start may not be greater than range end)")
            exit()
    return bounds


print(extract_bounds(input("Set Bounds: ")))