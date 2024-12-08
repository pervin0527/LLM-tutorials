## WizardLLM에서 소개한 방법
## 질문의 깊이와 너비를 확장시켜 instruction을 증강시키는 효과가 있음.

from openai import OpenAI
import json
import pandas as pd
from tqdm import tqdm
import os
import random
import random
import openpyxl
from datasets import load_dataset, Dataset,dataset_dict
import pandas as pd



def add_constraints(instruction,corpus,openai):
    
    evolving= f"저는 당신이 질문 재작성자로 활동하기를 원합니다. 당신의 목표는 주어진 질문 제공된 문장을 참고하여 재작성해, AI가 처리하기 더 어렵게 만드는 것입니다. 하지만 재작성된 질문은 합리적이어야 하고 인간이 이해하고 응답할 수 있어야 합니다.\n\
        다음 방법을 사용하여 주어진 질문을 더 복잡하게 하나만 만들어야 합니다:\n\
        - 주어진 질문에 제약 조건, 요구 사항을 하나 더 추가하십시오.\n\
        최대한 재작성된 질문이 장황해지지 않도록 노력해야 하며, 재작성된 질문은 주어진 질문에 단어를 10~20개만 추가할 수 있으며, 답변없이 질문 하나만 무조건 한국어로 재작성해주세요.\n\
        제공된 문장: {corpus}\n\n\
        주어진 질문: {instruction}\n\n\
        재작성된 질문: "
    
    chat_completion = openai.chat.completions.create(
        #model="mistralai/Mixtral-8x22B-Instruct-v0.1",
        model='microsoft/WizardLM-2-8x22B',
        messages=[{"role:":"user", "content" : evolving}],
        temperature=0.7,
        max_tokens=8192)
    
    return chat_completion.choices[0].message.content



def deepning(instruction,corpus,openai):
    
    evolving= f"저는 당신이 질문 재작성자로 활동하기를 원합니다. 당신의 목표는 주어진 질문을 제공된 문장을 참고하여 재작성해, AI가 처리하기 더 어렵게 만드는 것입니다. 하지만 재작성된 질문은 합리적이어야 하고 인간이 이해하고 응답할 수 있어야 합니다.\n\
        다음 방법을 사용하여 주어진 질문을 더 복잡하게 하나만 만들어야 합니다:\n\
        - 주어진 프롬프트에 특정 문제에 대해 깊이와 폭을 추가하십시오.\n\
        최대한 재작성된 질문이 장황해지지 않도록 노력해야 하며, 재작성된 질문은 주어진 질문에 단어를 10~20개만 추가할 수 있으며, 답변없이 질문 하나만 무조건 한국어로 재작성해주세요.\n\
        제공된 문장: {corpus}\n\n\
        주어진 질문: {instruction}\n\n\
        재작성된 질문: "
    
    chat_completion = openai.chat.completions.create(
        #model="mistralai/Mixtral-8x22B-Instruct-v0.1",
        model='microsoft/WizardLM-2-8x22B',
        messages=[{"role:":"user", "content" : evolving}],
        temperature=0.7,
        max_tokens=8192)
    
    return chat_completion.choices[0].message.content



def increase_reasoning(instruction,corpus,openai):
    
    evolving= f"저는 당신이 질문 재작성자로 활동하기를 원합니다. 당신의 목표는 주어진 질문을 제공된 문장을 참고하여 재작성해, AI가 처리하기 더 어렵게 만드는 것입니다. 하지만 재작성된 질문은 합리적이어야 하고 인간이 이해하고 응답할 수 있어야 합니다.\n\
        다음 방법을 사용하여 주어진 질문을 더 복잡하게 하나만 만들어야 합니다:\n\
        - 간단한 사고 과정만으로 해결할 수 있는 문제라면 여러 단계의 추론을 명시적으로 요구하도록 재작성하십시오.\n\
        최대한 재작성된 질문이 장황해지지 않도록 노력해야 하며, 재작성된 질문은 주어진 질문에 단어를 10~20개만 추가할 수 있으며, 답변없이 질문 하나만 무조건 한국어로 재작성해주세요.\n\
        제공된 문장: {corpus}\n\n\
        주어진 질문: {instruction}\n\n\
        재작성된 질문: "
    
    chat_completion = openai.chat.completions.create(
        #model="mistralai/Mixtral-8x22B-Instruct-v0.1",
        model='microsoft/WizardLM-2-8x22B',
        messages=[{"role:":"user", "content" : evolving}],
        temperature=0.7,
        max_tokens=8192)
    
    return chat_completion.choices[0].message.content




def concretizing(instruction,corpus,openai):
    
    evolving= f"저는 당신이 질문 재작성자로 활동하기를 원합니다. 당신의 목표는 주어진 질문을 제공된 문장을 참고하여 재작성해, AI가 처리하기 더 어렵게 만드는 것입니다. 하지만 재작성된 질문은 합리적이어야 하고 인간이 이해하고 응답할 수 있어야 합니다.\n\
        재작성할 때, 비텍스트 부분(표, 코드 등)을 생략해서는 안 됩니다. 또한 주어진 질문의 입력 부분을 생략하지 마십시오.\n\
        다음 방법을 사용하여 주어진 질문을 더 복잡하게 하나만 만들어야 합니다:\n\
        - 일반 개념을 더 구체적인 개념으로 바꾸십시오.\n\
        최대한 재작성된 질문이 장황해지지 않도록 노력해야 하며, 재작성된 질문은 주어진 질문에 단어를 10~20개만 추가할 수 있으며, 답변없이 질문 하나만 무조건 한국어로 재작성해주세요.\n\
        제공된 문장: {corpus}\n\n\
        주어진 질문: {instruction}\n\n\
        재작성된 질문: "
    
    chat_completion = openai.chat.completions.create(
        #model="mistralai/Mixtral-8x22B-Instruct-v0.1",
        model='microsoft/WizardLM-2-8x22B',
        messages=[{"role:":"user", "content" : evolving}],
        temperature=0.7,
        max_tokens=8192)
    
    return chat_completion.choices[0].message.content



# 수식 데이터 혹은 코딩데이터등을 모아서 가는걸로.... 이외는 Pass !!!

def complicated_input(instruction,corpus,openai):
    
    evolving= f"저는 당신이 질문 재작성자로 활동하기를 원합니다. 당신의 목표는 주어진 질문을 제공된 문장을 참고하여 재작성해, AI가 처리하기 더 어렵게 만드는 것입니다. 하지만 재작성된 질문은 합리적이어야 하고 인간이 이해하고 응답할 수 있어야 합니다.\n\
        다음 방법을 사용하여 주어진 질문을 더 복잡하게 하나만 만들어야 합니다:\n\
        - 질문의 형식을 수식, 표나 코드등으로 등 복잡한 형태의 데이터로 변환하세요.\n\
        최대한 재작성된 질문이 장황해지지 않도록 노력해야 하며, 재작성된 질문은 주어진 질문에 단어를 10~20개만 추가할 수 있으며, 답변없이 질문 하나만 무조건 한국어로 재작성해주세요.\n\
        제공된 문장: {corpus}\n\n\
        주어진 질문: {instruction}\n\n\
        재작성된 질문: "
    
    chat_completion = openai.chat.completions.create(
        #model="mistralai/Mixtral-8x22B-Instruct-v0.1",
        model='microsoft/WizardLM-2-8x22B',
        messages=[{"role:":"user", "content" : evolving}],
        temperature=0.7,
        max_tokens=8192)
    
    return chat_completion.choices[0].message.content



def in_breadth_evolving(instruction,corpus,openai):
    
    evolving= f"당신은 새로운 질문을 창작하는 창작자 입니다.\
        당신의 목표는 주어진 질문에서 영감을 받아 제공된 문장을 참고하여 완전히 새로운 질문을 만드는 것입니다.\n\
        이 새로운 질문은 주어진 질문과 동일한 도메인에 속해야 하지만 더 드문 주제를 다루어야 합니다.\
        새로 만든 질문의 길이와 난이도는 주어진 질문과 비슷해야 합니다.\
        새로 만든 질문 합리적이어야 하고 인간이 이해하고 응답할 수 있어야 합니다.\
        새로 만든 질문을 답변없이 질문 하나만 무조건 한국어로 재작성해주세요. 기존의 질문은 답변에 포함되지 않아야 합니다.\n\
        제공된 문장: {corpus}\n\n\
        주어진 질문: {instruction}\n\n\
        새로 만든 질문: "
    
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

    


    df= pd.read_excel('final_evolving_insurance.xlsx')

    #df= df.reset_index(drop=True)

    
    query=[]
    corpus_lst=[]
    origin_lst=[]
    i=0

    while i< len(df):

        flag_a=False
        flag_b=False
        flag_c=False


        picked=random.sample([1,2,3,4],2)
        
        add_lst=[]
        corpus=df['corpus'][i]
        origin=df['instruction'][i]
        if 1 in picked:
            query_a = add_constraints(df['instruction'][i],corpus,openai).lstrip()
            add_lst.append(query_a)

        if 2 in picked:
            query_a = deepning(df['instruction'][i],corpus,openai).lstrip()
            add_lst.append(query_a)

        if 3 in picked:
            query_a = increase_reasoning(df['instruction'][i],corpus,openai).lstrip()
            add_lst.append(query_a)

        if 4 in picked:
            query_a = concretizing(df['instruction'][i],corpus,openai).lstrip()
            add_lst.append(query_a)


        query_b=in_breadth_evolving(df['instruction'][i],corpus,openai).lstrip()
        add_lst.append(query_b)

        
        if (len(add_lst)==3) and len(add_lst[0])>5 and  len(add_lst[1])>5:

            flag_a=True
            flag_b=True
            flag_c=True


        if flag_a==flag_b==flag_c==True:

            query+=add_lst
            corpus_lst+=[corpus,corpus,corpus]
            origin_lst+=[origin,origin,origin]
            
            
            print(f'{i+1}/{len(df)} data was saved')
            
            i+=1


    

    maded_df= pd.DataFrame({'instruction': query,'corpus':corpus_lst,'orgin':origin_lst})

    maded_df.to_excel('insurance_evol2.xlsx',index=False)


    print('================================================================================================================\n\n')
    
    print(f'{"Evolving was finished":^50}')
    
    print('================================================================================================================')



main()