import random
from openai import OpenAI
import json
import pandas as pd
from tqdm import tqdm
import os
import random
import openpyxl
from datasets import load_dataset, Dataset,dataset_dict
import pandas as pd




def generate_response(instruction,corpus,openai):
    
    evolving= f"다음 질문에 대해서, 주어진 문단을 기반으로 근거를 가지고 논리적으로 정확하게 한국어로만 답변하세요.\n\
        주어진 문장: {corpus}\n\n\
        질문: {instruction}\n\n\
        답변: "
    
    chat_completion = openai.chat.completions.create(
        #model="mistralai/Mixtral-8x22B-Instruct-v0.1",
        model='microsoft/WizardLM-2-8x22B',
        messages=[{"role:":"user", "content" : evolving}],
        temperature=0.7,
        max_tokens=8192)
    
    return chat_completion.choices[0].message.content




def main():
    # Create an OpenAI client with your deepinfra token and endpoint
    openai = OpenAI(
        api_key="your_api_key",
        base_url="https://api.deepinfra.com/v1/openai",)


    df= pd.read_excel('insurance_evol2.xlsx')


    i= 0
    res=[]


    while i< len(df):
        
        ans = generate_response(df['instruction'][i],df['corpus'][i],openai).lstrip()

        if len(ans)>3:
            
            res.append(ans)
            i+=1

            
            print(f'{i}/{len(df)} data was saved')

        
        else:
            pass


    df['response'] = res

    df.to_excel('insurance-QA-set_SEED2.xlsx',index=False)

    print('================================================================================================================\n\n')
    print(f'{"Generating Data was finished!!":^50}\n')
    print('================================================================================================================')






main()








