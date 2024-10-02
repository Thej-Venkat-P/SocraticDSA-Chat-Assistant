import openai
import gradio as gr

glhf_key = "glhf_07eceec28a9d9d79d88c97e9e0900eb2"
client = openai.OpenAI(
    api_key=glhf_key,
    base_url="https://glhf.chat/api/openai/v1",
)

model_name = "hf:meta-llama/Meta-Llama-3.1-405B-Instruct"

def alpaca_format(messages):
    conversation = []
    for message in messages:
        role = message["role"]
        content = message["content"]
        conversation.append(f"{role}: {content}")
    return "\n".join(conversation)

def get_previous_context(messages):
    conversation = alpaca_format(messages)
    prompt = f"For the following Conversation, your task is only to summarize it \
        but include all the important details besides any pseudocode or code snippets.\
        And do not add any additional information or assume any information besides \
        what is given in the following conversation.\
        \n\nConversation:\n{conversation}\n\nSummary:"
    completions = client.completions.create(
        stream=False,
        model="hf:mistralai/Mixtral-8x7B-Instruct-v0.1",
        prompt=prompt,
        max_tokens=None,
    )
    
    full_response = completions.choices[0].text.split("\n")
    return "".join(full_response)

def get_chat_response():
    completions = client.chat.completions.create(
        stream=True,
        model=model_name,
        messages=chat_messages,
    )
    
    response = []
    for chunk in completions:
        if chunk.choices[0].delta.content is not None:
            response.append(str(chunk.choices[0].delta.content))
    return "".join(response)

chat_messages = [
    {
    "role": "system",
    "content": "You are a teaching assistant and your task is to teach a student using the Socratic teaching method.\
        The Socratic method is where the assistant asks probing questions and leads the student to the answer instead of revealing the answer. \
        You excel in Data Structures and Algorithms and teach in a soft and patient tone guiding and probing the student to answer to your questions.\
        You can also ask the Student to write pseudocode or code in any language in the pseudocode editor to make them practice.\
        Also mentions to the student if the particular pseudocode is inefficient in any way and how to improve it.\
        Introduce yourself to the student as SocraticDSA and ask the student to introduce themselves.",
    },
]

def check_messages_length():
    global chat_messages
    if len(chat_messages) > 8:
        first_message = chat_messages[0:1]
        last_two_messages = chat_messages[-2:]
        previous_context = get_previous_context(chat_messages[:-2])
        previous_context = {
            "role": "system",
            "content": "Here is a summary of the previous conversation:\n" + previous_context,
        }
        chat_messages = first_message + [previous_context] + last_two_messages

def get_assistant_response(user_message="", pseudocode="", verbose_memory=False):
    global chat_messages
    if user_message:
        chat_messages.append({"role": "user", "content": user_message})
    if pseudocode:
        chat_messages.append({"role": "system", "content": f"Here is the pseudocode/code written by the student:\n{pseudocode}"})
    response = get_chat_response()
    chat_messages.append({"role": "assistant", "content": response})
    check_messages_length()
    if verbose_memory:
        print("Chat Messages:\n")
        for message in chat_messages:
            print(f"{message['role']}: {message['content']}\n")
    return response

def test_get_previous_content():
    # Unit test for get_previous_context
    chat_messages.append({"role": "user", "content": "What is a linked list?"})
    chat_messages.append({"role": "assistant", "content": "A linked list is a linear data structure where each element is a separate object."})
    chat_messages.append({"role": "user", "content": "What are the types of linked lists?"})
    chat_messages.append({"role": "assistant", "content": "There are singly linked lists, doubly linked lists, and circular linked lists."})
    chat_messages.append({"role": "user", "content": "Can you explain a doubly linked list?"})
    chat_messages.append({"role": "assistant", "content": "A doubly linked list is a linked list where each node contains a reference to the previous and the next node."})
    chat_messages.append({"role": "user", "content": "What are the advantages of a doubly linked list?"})
    chat_messages.append({"role": "assistant", "content": "A doubly linked list allows traversal in both directions, insertion and deletion of nodes without traversing the entire list."})
    print(get_previous_context(chat_messages))


# Building a gradio app to interact with the assistant

def socratic_chat(User_Input, Pseudocode=""):
    return get_assistant_response(User_Input, Pseudocode)

iface = gr.Interface(
    fn=socratic_chat,
    inputs=[
        gr.Textbox(lines=2, placeholder="Enter your message here...", label="User Input"),
        gr.Textbox(lines=2, placeholder="Enter pseudocode here (optional)(Use spaces for indentation)...", label="Pseudocode", interactive=True),
    ],
    outputs=gr.Textbox(label="SocraticDSA"),
    title="Socratic Chat Assistant",
)

iface.launch(server_port=8000)

run_main = False
if __name__ == "__main__" and run_main:
    print("Welcome to Socratic Chat!")
    print("SocraticDSA: ", get_assistant_response(""))
    print()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "stop", "quit"]:
            break
        print(get_assistant_response(user_input))
        print()
