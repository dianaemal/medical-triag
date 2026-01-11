import json
import json
from pathlib import Path
import os
def load_json(path):
    with open(path, 'r') as file:
        data = json.load(file)

    return data



def create_document(json_data):
    documents = []


    condition = json_data["condition"]

    for key, value in json_data.items():

        if key not in ["condition", "synonyms"]:

            #dic["text"] = value
            if key == "symptoms":
                urgency = "medium"
            elif key == "red_flags":
                urgency = "high"
            else:
                urgency = "low"
            metadata = {"condition": condition, "section": key, "urgency": urgency }

            if isinstance(value, list):
                text = ", ".join(value)
            elif isinstance(value, dict):
                text = json.dumps(value, indent=2)
            else:
                text = str(value)

            document = {
                "text": text,
                "metadata": metadata
            }
            documents.append(document)

    return documents

def save_documents(documents, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as file:
        json.dump(documents, file, indent=2)


if __name__ == "__main__":

    file_names = os.listdir("../data/raw")

    for f in file_names:
        data = load_json(f"../data/raw/{f}")
        documents = create_document(data)
        new_name, _ = f.split(".")
        output_path = Path(f"../data/processed/{new_name}_docs.json")
        save_documents(documents, output_path)

#data = load_json("../data/raw/sore_throat.json")
#documents = create_document(data)
#output_path = Path("../data/processed/sore_throat_docs.json")
#save_documents(documents, output_path)

#for doc in documents:
   # print("----")
    #print("TEXT:")
    #print(doc["text"])
    #print("METADATA:")
    #print(doc["metadata"])

    