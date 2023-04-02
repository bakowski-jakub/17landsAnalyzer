import json

set = "one"
oracle = "oracle-cards-20230401090233.json"
outputFile = str(set) + "_oracle.json"

def oraclePruner(set, input):
    with open (outputFile, 'w') as outfile:
        for key in range(len(input)):
            if input[key]['set'] == set:
                outfile.write(json.dumps(input[key])+"\n")

if __name__ == "__main__":
    f = open(oracle, encoding="utf8")
    jsonObject = json.load(f)
    oraclePruner(set, jsonObject)