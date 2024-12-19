import os
import json
import openai
import streamlit as st

from utils.file import load_json, save_to_json_file
from processors.cot_prompt_processor import prompt_input_processing, run_openai_api
from processors.data_processor import translate_and_convert_to_string, process_vision_result, extract_workstyle_info
from utils.calculates import create_results_dataframe, analyze_responses, visualize_results, analyze_unique_responses

from processors.prompt_processor import vision_prompt, workstyle_prompt, summary_prompt
from processors.cot_prompt_processor import (vision_prompt as cot_vision_prompt, 
                                             workstyle_prompt as cot_workstyle_prompt, 
                                             summary_prompt as cot_summary_prompt)


from dotenv import load_dotenv
load_dotenv('/home/pervinco/LLM-tutorials/keys.env')
openai_api_key = os.getenv('GRAVY_LAB_OPENAI')

def main():
    n_iter = 1
    temperature = 0
    client = openai.OpenAI(api_key=openai_api_key)
    dataset = load_json("../data/dev-survey-result.json")
    print(f"Total data : {len(dataset)}")

    vision_results = []
    workstyle_results = []
    summary_results = []
    for idx, hr_data_dict in enumerate(dataset):
        vision_data = process_vision_result(hr_data_dict['visionResult'], hr_data_dict['summaryResult'])
        workstyle_data = extract_workstyle_info(hr_data_dict['workstyleResult'], hr_data_dict['summaryResult'])
        vision_input, workstyle_input, summary_input = prompt_input_processing(hr_data_dict, vision_data, workstyle_data)

        print("=" * 60)
        print(f"{idx:>04}\n")
        print(f"Vision input\n", vision_input)
        print(f"Workstyle input\n", workstyle_input)
        print(f"Summary input\n", summary_input)

        vision_results.append({"original" : run_openai_api(client, n_iter, vision_prompt, vision_input, temperature),
                               "advanced" : run_openai_api(client, n_iter, cot_vision_prompt, vision_input, temperature)})

        workstyle_results.append({"original" : run_openai_api(client, n_iter, workstyle_prompt, workstyle_input, temperature),
                                  "advanced" : run_openai_api(client, n_iter, cot_workstyle_prompt, workstyle_input, temperature)})
        
        summary_results.append({"original" : run_openai_api(client, n_iter, summary_prompt, summary_input, temperature),
                                "advanced" : run_openai_api(client, n_iter, cot_summary_prompt, summary_input, temperature)})
        
    save_to_json_file(vision_results, "../result/vision_output.json")
    save_to_json_file(workstyle_results, "../result/workstyle_output.json")
    save_to_json_file(summary_results, "../result/summary_output.json")
        

if __name__ == "__main__":
    main()