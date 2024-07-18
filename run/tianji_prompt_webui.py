import gradio as gr
import json
import random
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
from zhipuai import ZhipuAI
import os
file_path = 'D:/LLM/Tianji/tianji/prompt/yiyan_prompt/all_yiyan_prompt.json'
API_KEY = os.environ['ZHIPUAI_API_KEY']
CHOICES = ["敬酒","请客","送礼","送祝福","人际交流","化解尴尬","矛盾应对"]

with open(file_path, 'r', encoding='utf-8') as file:
    json_data = json.load(file)
    
def get_names_by_id(id):
    names = []
    for item in json_data:
        if 'id' in item and item['id'] == id:
            names.append(item['name'])
    
    return list(set(names))  # Remove duplicates


def get_system_prompt_by_name(name):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    """Returns the system prompt for the specified name."""
    for item in data:
        if item['name'] == name:
            return item['system_prompt']
    return None  # If the name is not found

def change_example(name,cls_choose_value,chatbot):
    now_example = []
    if chatbot is not None:
        print("切换场景清理bot历史")
        chatbot.clear()
    for i in cls_choose_value:
        if i['name'] == name:
            now_example = [[j['input'],j['output']] for j in i['example']]
    if now_example is []:
        raise gr.Error("获取example出错！")
    return gr.update(samples=now_example),chat_history

def random_button_click(chatbot):
    choice_number = random.randint(0, 6)
    now_id = choice_number + 1
    cls_choose = CHOICES[choice_number]
    now_json_data = _get_id_json_id(choice_number)
    random_name = [i['name'] for i in now_json_data]
    if chatbot is not None:
        print("切换场景清理bot历史")
        chatbot.clear()
    return cls_choose,now_json_data,gr.update(choices=get_names_by_id(now_id),value= random.choice(random_name))

def example_click(dataset,name,now_json):
    system = ""
    for i in now_json:
        if i['name'] == name:
            system = i['system_prompt']

    if system_prompt =="":
        print(name,now_json)
        raise '遇到代码问题，清重新选择场景'
    return dataset[0], system

def _get_id_json_id(idx):
    now_id = idx +1 # index + 1 
    now_id_json_data = []
    for item in json_data:
        if int(item['id']) == int(now_id):
            temp_dict = dict(name=item['name'],example=item['example'],system_prompt=item['system_prompt'])
            now_id_json_data.append(temp_dict)
    return now_id_json_data

def cls_choose_change(idx):
    now_id = idx +1
    return _get_id_json_id(idx),gr.update(choices=get_names_by_id(now_id),value=get_names_by_id(now_id)[0])

def combine_message_and_history(message, chat_history):
    # 将聊天历史中的每个元素（假设是元组）转换为字符串
    history_str = "\n".join(f"{sender}: {text}" for sender, text in chat_history)

    # 将新消息和聊天历史结合成一个字符串
    full_message = f"{history_str}\nUser: {message}"
    return full_message

def respond(system_prompt, message, chat_history):
    if len(chat_history) > 11:
        chat_history.clear()  # 清空聊天历史
        chat_history.append(['请注意',"对话超过 已重新开始"]) 
    # 合并消息和聊天历史
    message1 = combine_message_and_history(message, chat_history)
    print(message1)

    #调用智谱大模型回复
    # client = ZhipuAI(api_key=API_KEY)
    # response = client.chat.completions.create(
    #     model="glm-4",
    #     messages=[
    #         {"role": "system", "content": system_prompt},
    #         {"role": "user", "content": message1}
    #     ],
    # )
    #

    #调用OPENAI回复
    openai_api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_API_BASE')
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("user", "{message}")
    ])

    llm = ChatOpenAI(temperature=0.1,
                     api_key=openai_api_key,
                     base_url=base_url)

    chain = LLMChain(llm=llm, prompt=prompt_template, verbose=True)
    output = chain.run({
        "system_prompt": system_prompt,
        "message": message1
        })
    # output = llm.invoke(message1)

    print(output)

    # 提取模型生成的回复内容
    # bot_message_text = response.choices[0].message.content
    bot_message_text = output;
    # 更新聊天历史
    chat_history.append([message,bot_message_text])  # 用户的消息

    return "", chat_history


def clear_history(chat_history):
    chat_history.clear()
    return chat_history

def regenerate(chat_history,system_prompt):
    if chat_history:
        # 提取上一条输入消息
        last_message = chat_history[-1][0]
        # 移除最后一条记录
        chat_history.pop()
        # 使用上一条输入消息调用 respond 函数以生成新的回复
        msg,chat_history = respond(system_prompt, last_message, chat_history)
    # 返回更新后的聊天记录
    return msg, chat_history

TITLE = """
# Tianji 人情世故大模型系统——prompt版 欢迎star🤗！\n 
## 🤖感谢[智谱AI](https://www.zhipuai.cn/)的token支持！
## 开源项目地址：https://github.com/SocialAI-tianji/Tianji
## 使用方法：选择或随机一个场景，输入提示词（或者点击上面的Example自动填充），随后发送！
### 我们的愿景是构建一个从数据收集开始的大模型全栈垂直领域开源实践。\n
### 我们还有其他体验应用：知识库、agent、大模型微调，欢迎体验！更欢迎你的贡献！祝大家龙年快乐！
"""

with gr.Blocks() as demo:
    chat_history = gr.State()
    now_json_data = gr.State(value=_get_id_json_id(0))
    now_name = gr.State()
    gr.Markdown(TITLE)
    cls_choose = gr.Radio(label="请选择任务大类",choices=CHOICES,type="index",value="敬酒") 
    input_example = gr.Dataset(components=["text","text"],samples=[
                    ["请先选择合适的场景","请先选择合适的场景"],
                    ])
    with gr.Row():
        with gr.Column(scale=1):
            dorpdown_name = gr.Dropdown(choices=get_names_by_id(1),label='场景', info='请选择合适的场景',interactive=True)
            system_prompt = gr.TextArea(label='系统提示词') #TODO 需要给初始值嘛？包括example
            random_button = gr.Button('🪄点我随机一个试试！',size='lg')
            dorpdown_name.change(fn=get_system_prompt_by_name, inputs=[dorpdown_name], outputs=[system_prompt])
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(label='聊天界面', value=[['如果喜欢，请给我们一个⭐，谢谢', "不知道选哪个？试试点击随机按钮把！"]])
            msg = gr.Textbox(label="输入信息")
            msg.submit(respond, inputs=[system_prompt,msg, chatbot], outputs=[msg, chatbot])
            submit = gr.Button('发送').click(respond, inputs=[system_prompt,msg, chatbot], outputs=[msg, chatbot])
            with gr.Row():
                clear = gr.Button('记录删除').click(clear_history, inputs=[chatbot], outputs=[chatbot])
                regenerate = gr.Button('重新生成').click(regenerate, inputs=[chatbot,system_prompt], outputs = [msg, chatbot])

    cls_choose.change(fn=cls_choose_change,inputs=cls_choose,outputs=[now_json_data,dorpdown_name])
    dorpdown_name.change(fn=change_example,inputs = [dorpdown_name,now_json_data,chatbot], outputs=[input_example,chat_history])
    input_example.click(fn=example_click, inputs=[input_example,dorpdown_name,now_json_data],outputs=[msg,system_prompt] )
    random_button.click(fn=random_button_click,inputs=chatbot,outputs=[cls_choose,now_json_data,dorpdown_name])

if __name__ == "__main__":
    demo.launch()
