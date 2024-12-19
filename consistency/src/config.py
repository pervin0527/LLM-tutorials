gt_path = "../data/amy_gt.json"
data_path = "../data/amy_culture_fit.json"

llm_process = True
prompt_version = 1

n_iter = 30
num_gram = 4
temperature = 0.1
embed_model = "text-embedding-3-large"

output_dir = "../result"
csv_file_name = f"prompt_ver{prompt_version}-{n_iter}_samples.csv"