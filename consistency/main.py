import os
import json
import openai
import pandas as pd

from dotenv import load_dotenv
load_dotenv('/home/pervinco/LLM-tutorials/keys.env')
openai_api_key = os.getenv('GRAVY_LAB_OPENAI')

from config import *
from src.cot_prompt_processor import prompt_input_processing, run_openai_api
from src.data_processor import translate_and_convert_to_string, process_vision_result, extract_workstyle_info
from src.utils import create_results_dataframe, analyze_responses, visualize_results, analyze_unique_responses

def main():
    if prompt_version == 1:
        from src.prompt_processor import vision_prompt, workstyle_prompt, summary_prompt
    else:
        from src.cot_prompt_processor import vision_prompt, workstyle_prompt, summary_prompt

    client = openai.OpenAI(api_key=openai_api_key)
    with open(data_path, 'r', encoding='utf-8') as file:
        hr_data_dict = json.load(file)

    with open(data_path, 'r', encoding="utf-8") as file:
        gt_data_dict = json.load(file)

    if llm_process:
        processed_data_summary = translate_and_convert_to_string(hr_data_dict['summaryResult'])
        vision_data = process_vision_result(hr_data_dict['visionResult'], hr_data_dict['summaryResult'])
        workstyle_data = extract_workstyle_info(hr_data_dict['workstyleResult'], hr_data_dict['summaryResult'])
        vision_input, workstyle_input, summary_input = prompt_input_processing(hr_data_dict, vision_data, workstyle_data)
        print(f"Vision input\n", vision_input)
        print(f"Workstyle input\n", workstyle_input)
        print(f"Summary input\n", summary_input)

        vision_results = run_openai_api(client, n_iter, vision_prompt, vision_input, temperature)
        workstyle_results = run_openai_api(client, n_iter, workstyle_prompt, workstyle_input, temperature)
        summary_results = run_openai_api(client, n_iter, summary_prompt, summary_input, temperature)

        df = create_results_dataframe(vision_results, workstyle_results, summary_results)
        df.to_csv(os.path.join(output_dir, csv_file_name), index=False, encoding='utf-8-sig')
        print(f"Results saved to {os.path.join(output_dir, csv_file_name)}")

    df = pd.read_csv(f"{output_dir}/{csv_file_name}")
    analysis_results = analyze_responses(df, client, num_gram, embed_model)

    for response_type, metrics in analysis_results.items():
        print(f"\nResults for {response_type.upper()}:")
        print(f"Semantic Similarity (mean): {metrics['semantic_similarity']:.2f}")
        for n, similarity in enumerate(metrics['n_gram_similarities'], start=1):
            print(f"{n}-gram Similarity (mean): {similarity:.2f}")

    prefix = csv_file_name.split('.')[0]
    visualize_results(analysis_results, df, client, output_dir, prefix)
    analyze_unique_responses(df)

if __name__ == "__main__":
    main()