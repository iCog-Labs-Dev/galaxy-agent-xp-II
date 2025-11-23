import re

class WorkflowParser:
    def extract_io(self, readme: str):
        inputs = []
        outputs = []

        try:
            input_block = re.findall(r"Inputs(.*?)(Outputs|$)", readme, flags=re.S)[0][0]
            output_block = re.findall(r"Outputs(.*)", readme, flags=re.S)[0]

            inputs = [x.strip(" .") for x in input_block.split("\n") if x.strip()]
            outputs = [x.strip(" .") for x in output_block.split("\n") if x.strip()]
        except:
            pass
        
        return inputs, outputs
